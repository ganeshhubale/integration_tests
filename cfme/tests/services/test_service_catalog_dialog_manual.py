import pytest

from cfme import test_requirements

pytestmark = [
    pytest.mark.manual,
    test_requirements.service
]


@pytest.mark.manual
@pytest.mark.tier(2)
def test_notification_banner_vm_provisioning_notification_and_service_request_should_be_in_syn():
    """ Notification Banner - VM Provisioning Notification and Service Request should be in  Sync
    Polarion:
        assignee: nansari
        casecomponent: Services
        testtype: functional
        initialEstimate: 1/4h
        startsin: 5.7
        tags: service
    Bugzilla:
        1389312
    """
    pass


@pytest.mark.manual
@pytest.mark.tier(3)
def test_user_should_be_able_to_see_requests_irrespective_of_tags_assigned():
    """ User should be able to see requests irrespective of tags assigned
    Polarion:
        assignee: nansari
        casecomponent: Services
        initialEstimate: 1/4h
        testtype: functional
        startsin: 5.9
        tags: service
    Bugzilla:
        1641012
    """
    pass


@pytest.mark.manual
@pytest.mark.tier(3)
def test_changing_action_order_in_catalog_bundle_should_not_removes_resource():
    """
    Polarion:
        assignee: nansari
        casecomponent: Services
        initialEstimate: 1/16h
        testtype: functional
        startsin: 5.8
        tags: service
    Bugzilla:
        1615853
    """
    pass


@pytest.mark.manual
@pytest.mark.tier(2)
def test_notification_banner_service_event_should_be_shown_in_notification_bell():
    """
    Polarion:
        assignee: nansari
        casecomponent: Services
        initialEstimate: 1/4h
        testtype: functional
        startsin: 5.9
        tags: service
        testSteps:
            1. OPS UI  and SSUI service requests should create an event in notification bell
            2. Also check , Clear All and "MArk as read" in notification bell
            3. Number of events shown in notification bell
    """
    pass


@pytest.mark.manual
@pytest.mark.tier(2)
def test_custom_image_on_item_bundle_crud():
    """
    Polarion:
        assignee: nansari
        casecomponent: Services
        testtype: functional
        initialEstimate: 1/8h
        startsin: 5.5
        tags: service
        testSteps:
            1. Create a catalog item
            2. Upload custom image
            3. remove custom image
            4. Create a catalog  bundle
            5. Upload a custom image
            6. Change custom image
        expectedResults:
            1.
            2. No error seen
            3.
            4.
            5. No error seen
    Bugzilla:
        1487056
    """
    pass


@pytest.mark.manual
@pytest.mark.tier(3)
def test_request_filter_on_request_page():
    """
    Polarion:
        assignee: nansari
        casecomponent: Services
        testtype: functional
        initialEstimate: 1/4h
        startsin: 5.9
        tags: service
    Bugzilla:
        1498237
    """
    pass
