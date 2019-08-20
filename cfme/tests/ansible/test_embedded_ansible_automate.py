# -*- coding: utf-8 -*-
import fauxfactory
import pytest

from cfme import test_requirements
from cfme.automate.simulation import simulate
from cfme.control.explorer import alert_profiles
from cfme.fixtures.automate import DatastoreImport
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.markers.env_markers.provider import ONE_PER_TYPE
from cfme.services.service_catalogs import ServiceCatalogs
from cfme.services.service_catalogs.ui import OrderServiceCatalogView
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.conf import credentials
from cfme.utils.log_validator import LogValidator
from cfme.utils.update import update
from cfme.utils.wait import TimedOutError
from cfme.utils.wait import wait_for

pytestmark = [
    pytest.mark.long_running,
    pytest.mark.ignore_stream("upstream"),
    pytest.mark.provider([VMwareProvider], selector=ONE_PER_TYPE, scope="module"),
    test_requirements.ansible,
    pytest.mark.tier(3),
]


@pytest.fixture(scope="module")
def ansible_credential(appliance, ansible_repository, full_template_modscope):
    credential = appliance.collections.ansible_credentials.create(
        fauxfactory.gen_alpha(),
        "Machine",
        username=credentials[full_template_modscope["creds"]]["username"],
        password=credentials[full_template_modscope["creds"]]["password"]
    )
    yield credential
    credential.delete_if_exists()


@pytest.fixture
def management_event_class(appliance, namespace):
    appliance.collections.domains.instantiate(
        "ManageIQ").namespaces.instantiate(
        "System").namespaces.instantiate(
        "Event").namespaces.instantiate(
        "CustomEvent").classes.instantiate(
        name="Alert").copy_to(namespace.domain)
    return appliance.collections.domains.instantiate(
        namespace.domain.name).namespaces.instantiate(
        "System").namespaces.instantiate(
        "Event").namespaces.instantiate(
        "CustomEvent").classes.instantiate(name="Alert")


@pytest.fixture
def management_event_method(management_event_class, ansible_repository):
    return management_event_class.methods.create(
        name=fauxfactory.gen_alphanumeric(),
        location="playbook",
        repository=ansible_repository.name,
        playbook="copy_file_example.yml",
        machine_credential="CFME Default Credential",
        playbook_input_parameters=[("key", "value", "string")]
    )


@pytest.fixture
def management_event_instance(management_event_class, management_event_method):
    return management_event_class.instances.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        fields={"meth1": {"value": management_event_method.name}}
    )


@pytest.fixture(scope="module")
def custom_vm_button(appliance, ansible_catalog_item):
    buttongroup = appliance.collections.button_groups.create(
        text=fauxfactory.gen_alphanumeric(),
        hover="btn_desc_{}".format(fauxfactory.gen_alphanumeric()),
        type=appliance.collections.button_groups.VM_INSTANCE)
    button = buttongroup.buttons.create(
        type="Ansible Playbook",
        text=fauxfactory.gen_alphanumeric(),
        hover="btn_hvr_{}".format(fauxfactory.gen_alphanumeric()),
        playbook_cat_item=ansible_catalog_item.name)
    yield button
    button.delete_if_exists()
    buttongroup.delete_if_exists()


@pytest.fixture
def alert(appliance, management_event_instance):
    _alert = appliance.collections.alerts.create(
        "Trigger by Un-Tag Complete {}".format(fauxfactory.gen_alpha(length=4)),
        active=True,
        based_on="VM and Instance",
        evaluate="Nothing",
        driving_event="Company Tag: Un-Tag Complete",
        notification_frequency="1 Minute",
        mgmt_event=management_event_instance.name,
    )
    yield _alert
    _alert.delete_if_exists()


@pytest.fixture
def alert_profile(appliance, alert, full_template_vm_modscope):
    _alert_profile = appliance.collections.alert_profiles.create(
        alert_profiles.VMInstanceAlertProfile,
        "Alert profile for {}".format(full_template_vm_modscope.name),
        alerts=[alert]
    )
    _alert_profile.assign_to("The Enterprise")
    yield
    _alert_profile.delete_if_exists()


@pytest.mark.meta(automates=[1729999])
def test_automate_ansible_playbook_method_type_crud(appliance, ansible_repository, klass):
    """CRUD test for ansible playbook method.

    Bugzilla:
        1729999
        1740769

    Polarion:
        assignee: ghubale
        casecomponent: Automate
        initialEstimate: 1/12h
    """
    method = klass.methods.create(
        name=fauxfactory.gen_alphanumeric(),
        location="playbook",
        repository=ansible_repository.name,
        playbook="copy_file_example.yml",
        machine_credential="CFME Default Credential",
        playbook_input_parameters=[("key", "value", "string")]
    )
    with update(method):
        method.name = fauxfactory.gen_alphanumeric()
    method.delete()


def test_automate_ansible_playbook_method_type(request, appliance, ansible_repository, domain,
                                               namespace, klass):
    """Tests execution an ansible playbook via ansible playbook method using Simulation.

    Polarion:
        assignee: ghubale
        casecomponent: Automate
        initialEstimate: 1/4h
    """
    klass.schema.add_field(name="execute", type="Method", data_type="String")
    method = klass.methods.create(
        name=fauxfactory.gen_alphanumeric(),
        location="playbook",
        repository=ansible_repository.name,
        playbook="copy_file_example.yml",
        machine_credential="CFME Default Credential",
        playbook_input_parameters=[("key", "value", "string")]
    )
    instance = klass.instances.create(
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        fields={"execute": {"value": method.name}})

    simulate(
        appliance=appliance,
        request="Call_Instance",
        attributes_values={
            "namespace": "{}/{}".format(domain.name, namespace.name),
            "class": klass.name,
            "instance": instance.name
        }
    )
    request.addfinalizer(lambda: appliance.ssh_client.run_command(
        '[[ -f "/var/tmp/modified-release" ]] && rm -f "/var/tmp/modified-release"'))
    assert appliance.ssh_client.run_command('[ -f "/var/tmp/modified-release" ]').success


def test_ansible_playbook_button_crud(ansible_catalog_item, appliance, request):
    """
    Polarion:
        assignee: sbulage
        casecomponent: Ansible
        caseimportance: medium
        initialEstimate: 1/6h
    """
    buttongroup = appliance.collections.button_groups.create(
        text=fauxfactory.gen_alphanumeric(),
        hover=fauxfactory.gen_alphanumeric(),
        type=appliance.collections.button_groups.VM_INSTANCE)
    request.addfinalizer(buttongroup.delete_if_exists)
    button = buttongroup.buttons.create(
        type='Ansible Playbook',
        text=fauxfactory.gen_alphanumeric(),
        hover=fauxfactory.gen_alphanumeric(),
        playbook_cat_item=ansible_catalog_item.name)
    request.addfinalizer(button.delete_if_exists)
    assert button.exists
    view = navigate_to(button, 'Details')
    assert view.text.text == button.text
    assert view.hover.text == button.hover
    edited_hover = "edited {}".format(fauxfactory.gen_alphanumeric())
    with update(button):
        button.hover = edited_hover
    assert button.exists
    view = navigate_to(button, 'Details')
    assert view.hover.text == edited_hover
    button.delete(cancel=True)
    assert button.exists
    button.delete()
    assert not button.exists


def test_embedded_ansible_custom_button_localhost(full_template_vm_modscope, custom_vm_button,
        appliance, ansible_service_request, ansible_service, ansible_catalog_item):
    """
    Polarion:
        assignee: sbulage
        casecomponent: Ansible
        initialEstimate: 1/4h
    """
    with update(custom_vm_button):
        custom_vm_button.inventory = "Localhost"
    view = navigate_to(full_template_vm_modscope, "Details")
    view.toolbar.custom_button(custom_vm_button.group.text).item_select(custom_vm_button.text)
    order_dialog_view = appliance.browser.create_view(OrderServiceCatalogView)
    order_dialog_view.submit_button.wait_displayed()
    order_dialog_view.fields("credential").fill("CFME Default Credential")
    order_dialog_view.submit_button.click()
    wait_for(ansible_service_request.exists, num_sec=600)
    ansible_service_request.wait_for_request()
    view = navigate_to(ansible_service, "Details")
    hosts = view.provisioning.details.get_text_of("Hosts")
    assert hosts == "localhost"
    assert view.provisioning.results.get_text_of("Status") == "successful"


def test_embedded_ansible_custom_button_target_machine(full_template_vm_modscope, custom_vm_button,
        ansible_credential, appliance, ansible_service_request, ansible_service):
    """
    Polarion:
        assignee: sbulage
        casecomponent: Ansible
        initialEstimate: 1/4h
    """
    with update(custom_vm_button):
        custom_vm_button.inventory = "Target Machine"
    view = navigate_to(full_template_vm_modscope, "Details")
    view.toolbar.custom_button(custom_vm_button.group.text).item_select(custom_vm_button.text)
    order_dialog_view = appliance.browser.create_view(OrderServiceCatalogView)
    order_dialog_view.submit_button.wait_displayed()
    order_dialog_view.fields("credential").fill(ansible_credential.name)
    order_dialog_view.submit_button.click()
    wait_for(ansible_service_request.exists, num_sec=600)
    ansible_service_request.wait_for_request()
    view = navigate_to(ansible_service, "Details")
    hosts = view.provisioning.details.get_text_of("Hosts")
    assert hosts == full_template_vm_modscope.ip_address
    assert view.provisioning.results.get_text_of("Status") == "successful"


def test_embedded_ansible_custom_button_specific_hosts(full_template_vm_modscope, custom_vm_button,
        ansible_credential, appliance, ansible_service_request, ansible_service):
    """
    Polarion:
        assignee: sbulage
        casecomponent: Ansible
        initialEstimate: 1/4h
    """
    with update(custom_vm_button):
        custom_vm_button.inventory = "Specific Hosts"
        custom_vm_button.hosts = full_template_vm_modscope.ip_address
    view = navigate_to(full_template_vm_modscope, "Details")
    view.toolbar.custom_button(custom_vm_button.group.text).item_select(custom_vm_button.text)
    order_dialog_view = appliance.browser.create_view(OrderServiceCatalogView)
    order_dialog_view.submit_button.wait_displayed()
    order_dialog_view.fields("credential").fill(ansible_credential.name)
    order_dialog_view.submit_button.click()
    wait_for(ansible_service_request.exists, num_sec=600)
    ansible_service_request.wait_for_request()
    view = navigate_to(ansible_service, "Details")
    hosts = view.provisioning.details.get_text_of("Hosts")
    assert hosts == full_template_vm_modscope.ip_address
    assert view.provisioning.results.get_text_of("Status") == "successful"


@test_requirements.alert
def test_alert_run_ansible_playbook(full_template_vm_modscope, alert_profile, request, appliance):
    """Tests execution of an ansible playbook method by triggering a management event from an
    alert.

    Polarion:
        assignee: jdupuy
        casecomponent: Control
        initialEstimate: 1/6h
    """
    added_tag = full_template_vm_modscope.add_tag()
    full_template_vm_modscope.remove_tag(added_tag)
    request.addfinalizer(lambda: appliance.ssh_client.run_command(
        '[[ -f "/var/tmp/modified-release" ]] && rm -f "/var/tmp/modified-release"'))
    try:
        wait_for(
            lambda: appliance.ssh_client.run_command('[ -f "/var/tmp/modified-release" ]').success,
            timeout=60)
    except TimedOutError:
        pytest.fail("Ansible playbook method hasn't been executed.")


@pytest.fixture(scope='module')
def setup_ansible_repository(appliance, wait_for_ansible):
    repositories = appliance.collections.ansible_repositories
    repository = repositories.create(
        name="billy",
        url="https://github.com/billfitzgerald0120/ansible_playbooks",
        description=fauxfactory.gen_alpha()
    )
    view = navigate_to(repository, "Details")
    wait_for(
        lambda: view.entities.summary("Properties").get_text_of("Status") == "successful",
        timeout=60,
        fail_func=view.toolbar.refresh.click
    )
    yield
    repository.delete_if_exists()


@pytest.mark.tier(2)
@pytest.mark.meta(automates=[1678132])
@pytest.mark.ignore_stream("5.10")
@pytest.mark.parametrize(
    ("import_data", "item"),
    ([DatastoreImport("automate_domain_bz_1678135.zip", "Ansible_State_Machine_for_Ansible_stats3",
                      None, "using CFME creds"), "CatalogItemInitialization_jira23"],
     [DatastoreImport("automate_domain_bz_1678135.zip", "Ansible_State_Machine_for_Ansible_stats3",
                      None, "using CFME creds"), "CatalogItemInitialization_jira24"]),
    ids=["method_to_playbook", "playbook_to_playbook"]
)
def test_variable_pass(request, appliance, setup_ansible_repository, import_datastore, import_data,
                       item, dialog, catalog):
    """
    Bugzilla:
        1678132

    Polarion:
        assignee: ghubale
        initialEstimate: 1/8h
        caseposneg: positive
        casecomponent: Automate
        startsin: 5.11
        setup:
            1. Enable embedded ansible role
        testSteps:
            1. Add Ansible repo called billy -
               https://github.com/ManageIQ/integration_tests_playbooks
            2. Copy Export zip (Ansible_State_Machine_for_Ansible_stats3.zip ) to downloads
               directory(Zip file with description - 'Automate domain' is attached with BZ(1678135)
            3. Go to Automation/Automate Import/Export and import zip file
            4. Click on "Toggle All/None" and hit the submit button
            5. Go to Automation/Automate/Explorer and Enable the imported domain
            6. Make sure all the playbook methods have all the information (see if Repository,
               Playbook and Machine credentials have values), update if needed
            7. Import or create hello_world (simple ansible dialog with Machine credentials and
               hosts fields)
            8. Create a Generic service using the hello_world dialog and select instance
               'CatalogItemInitialization_jira23'(Note: This is the state machine which executes
               playbooks and inline method successively) then order service
            9. Run "grep dump_vars2 automation.log" from log directory
        expectedResults:
            1. Ansible repository added
            2.
            3.
            4. Domain imported
            5. Domain enabled
            6. Playbook method updated(if needed as mentioned in step)
            7. Ansible dialog created
            8. Generic service catalog item created
            9. Variables should be passed through successive playbooks and you should see logs like
               this(https://bugzilla.redhat.com/show_bug.cgi?id=1678132#c5)
    """
    # Making provisioning entry points to select while creating generic catalog items
    entry_point = (
        "Datastore",
        f"{import_datastore.name}",
        "Service",
        "Provisioning",
        "StateMachines",
        "ServiceProvision_Template",
        f"{item}",
    )

    # Creating generic catalog items
    catalog_item = appliance.collections.catalog_items.create(
        appliance.collections.catalog_items.GENERIC,
        name=fauxfactory.gen_alphanumeric(),
        description=fauxfactory.gen_alphanumeric(),
        display_in=True,
        catalog=catalog,
        dialog=dialog,
        provisioning_entry_point=entry_point,
    )

    with LogValidator(
        "/var/www/miq/vmdb/log/automation.log",
        matched_patterns=[
            ".*if Fred is married to Wilma and Barney is married to Betty and Peebles and BamBam "
            "are the kids, then the tests work !!!.*"
        ],
    ).waiting(timeout=120):
        # Ordering service catalog bundle
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        request_description = "Provisioning Service [{0}] from [{0}]".format(catalog_item.name)
        provision_request = appliance.collections.requests.instantiate(request_description)
        provision_request.wait_for_request(method="ui")
        request.addfinalizer(provision_request.remove_request)
