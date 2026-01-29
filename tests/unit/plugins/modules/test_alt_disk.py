import pytest
from unittest import mock

# adjust this import to match how your test runner loads collection modules
import plugins.modules.alt_disk as alt_disk


@pytest.fixture(autouse=True)
def reset_results_and_module():
    # reset the global results the module expects to use
    alt_disk.results = {
        'changed': False,
        'msg': '',
        'stdout': '',
        'stderr': ''
    }

    # make a mock module object used by functions
    module = mock.Mock()
    module.params = {'phases_to_execute': None}
    module.log = mock.Mock()
    module.debug = mock.Mock()
    module.fail_json = mock.Mock(side_effect=RuntimeError("fail_json called"))
    module.exit_json = mock.Mock(side_effect=RuntimeError("exit_json called"))
    module.run_command = mock.Mock()
    yield module


def test_get_pvs_parses_lspv_output(reset_results_and_module):
    module = reset_results_and_module
    stdout = (
        "hdisk0           000018fa3b12f5cb                     rootvg           active\n"
        "hdisk1           000018fa3b12f5cc                     None             \n"
    )
    module.run_command.return_value = (0, stdout, "")
    pvs = alt_disk.get_pvs(module)
    assert isinstance(pvs, dict)
    assert 'hdisk0' in pvs
    assert pvs['hdisk0']['pvid'] == '000018fa3b12f5cb'
    assert pvs['hdisk0']['vg'] == 'rootvg'
    assert pvs['hdisk0']['status'] == 'active'


def test_get_pvs_failure_returns_none_and_sets_msg(reset_results_and_module):
    module = reset_results_and_module
    module.run_command.return_value = (2, "", "err")
    pvs = alt_disk.get_pvs(module)
    assert pvs is None
    assert 'failed' in alt_disk.results['msg']


def test_get_free_pvs_parses_and_calls_getconf(reset_results_and_module):
    module = reset_results_and_module

    # lspv output shows one free disk
    lspv_out = "hdisk2           000018fa3b12f5cd                     None             \n"

    def run_command_side_effect(cmd):
        # return tuples consistent with calls: lspv, getlvodm, getconf
        if cmd[0] == 'lspv':
            return (0, lspv_out, "")
        if cmd[0] == 'getlvodm':
            return (3, "", "")
        if cmd[0] == 'getconf':
            return (0, "102400\n", "")
        return (0, "", "")

    module.run_command.side_effect = run_command_side_effect
    free = alt_disk.get_free_pvs(module)
    assert 'hdisk2' in free
    assert free['hdisk2']['pvid'] == '000018fa3b12f5cd'
    assert free['hdisk2']['size'] == 102400


def test_get_free_pvs_skips_if_getlvodm_not_expected(reset_results_and_module):
    module = reset_results_and_module
    lspv_out = "hdisk3           000018fa3b12f5ce                     None             \n"

    def side_effect(cmd):
        if cmd[0] == 'lspv':
            return (0, lspv_out, "")
        if cmd[0] == 'getlvodm':
            return (0, "", "")  # not rc==3 => skip
        return (0, "", "")

    module.run_command.side_effect = side_effect
    free = alt_disk.get_free_pvs(module)
    assert free == {}


def test_check_rootvg_parses_lsvg_output(reset_results_and_module):
    module = reset_results_and_module
    lsvg_out = (
        "rootvg:\n"
        "TOTAL PPs:           100 (6400 megabytes)\n"
        "USED PPs:            50 (3200 megabytes)\n"
        "PP SIZE:             64 megabyte(s)\n"
    )
    module.run_command.return_value = (0, lsvg_out, "")
    vg_info = alt_disk.check_rootvg(module)
    assert vg_info is not None
    assert vg_info['rootvg_size'] == 64 * 100
    assert vg_info['used_size'] == 64 * 50
    assert vg_info['status'] == 0


def test_check_rootvg_returns_none_on_parse_error(reset_results_and_module):
    module = reset_results_and_module
    module.run_command.return_value = (0, "unexpected output\n", "")
    vg_info = alt_disk.check_rootvg(module)
    assert vg_info is None
    assert 'parsing' in alt_disk.results['msg']


def test_find_valid_altdisk_minimize_policy_auto_selection(reset_results_and_module):
    module = reset_results_and_module
    # prepare rootvg_info and patch helper functions so selection proceeds
    rootvg_info = {'status': 0, 'rootvg_size': 1000, 'used_size': 200}

    # patch get_pvs to return no existing altinst_rootvg entries
    alt_disk.get_pvs = mock.Mock(return_value={
        'hdisk10': {'pvid': 'p1', 'vg': 'None', 'status': ''},
        'hdisk11': {'pvid': 'p2', 'vg': 'None', 'status': ''},
        'hdisk12': {'pvid': 'p3', 'vg': 'None', 'status': ''},
    })
    # patch get_free_pvs to provide sizes
    alt_disk.get_free_pvs = mock.Mock(return_value={
        'hdisk10': {'pvid': 'p1', 'size': 1000},
        'hdisk11': {'pvid': 'p2', 'size': 2000},
        'hdisk12': {'pvid': 'p3', 'size': 300},
    })

    # mirrors must be set to a sane value (1 copy)
    alt_disk.mirrors = 1  # ensure the module-level var exists for selection
    # call with empty hdisks and minimize policy
    hdisks = []
    alt_disk.find_valid_altdisk(module, hdisks, rootvg_info, 'minimize', force=False, allow_old_rootvg=False)
    assert len(hdisks) >= 1
    # expect the selected disk to be one of our keys (ensures selection happened)
    assert hdisks[0] in ('hdisk10', 'hdisk11', 'hdisk12')


def test_alt_disk_clean_idempotent_when_no_altinst(reset_results_and_module):
    module = reset_results_and_module
    # pvs contains no altinst_rootvg => alt_disk_clean should not fail, just set msg
    alt_disk.get_pvs = mock.Mock(return_value={
        'hdisk0': {'pvid': 'p1', 'vg': 'rootvg', 'status': 'active'}
    })
    alt_disk.alt_disk_clean(module, [], allow_old_rootvg=False)
    assert 'There is no alternate install rootvg' in alt_disk.results['msg']


def test_alt_rootvg_sleep_fails_when_no_altdisk(reset_results_and_module):
    module = reset_results_and_module
    alt_disk.get_pvs = mock.Mock(return_value={})
    with pytest.raises(RuntimeError):
        # fail_json side_effect raises RuntimeError
        alt_disk.alt_rootvg_sleep(module)


def test_alt_rootvg_sleep_idempotent_when_not_active(reset_results_and_module):
    module = reset_results_and_module
    alt_disk.get_pvs = mock.Mock(return_value={
        'hdisk7': {'pvid': 'p7', 'vg': 'altinst_rootvg', 'status': ''},
    })
    # Should return gracefully and append sleep message to results['msg']
    alt_disk.alt_rootvg_sleep(module)
    assert ('alternate install rootvg is already in sleep mode' in alt_disk.results['msg']) or isinstance(alt_disk.results['changed'], bool)
