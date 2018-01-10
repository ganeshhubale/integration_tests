# -*- coding: utf-8 -*-
import pytest
import six

from cfme import test_requirements
from cfme.configure.settings import Visual
from cfme.cloud.availability_zone import AvailabilityZone, AvailabilityZoneAllView
from cfme.cloud.provider import CloudProvider, CloudProvidersView
from cfme.cloud.flavor import Flavor, FlavorAllView
from cfme.cloud.instance import Instance
from cfme.cloud.keypairs import KeyPairAllView
from cfme.cloud.stack import StackAllView
from cfme.cloud.tenant import TenantAllView
from cfme.utils.appliance.implementations.ui import navigate_to


pytestmark = [pytest.mark.tier(3),
              test_requirements.settings,
              pytest.mark.usefixtures("openstack_provider")]

# Dict values are views which are required to check correct landing pages.
landing_pages = {
    'Clouds / Providers': CloudProvidersView,
    'Clouds / Key Pairs': KeyPairAllView,
    'Clouds / Tenants': TenantAllView,
    'Clouds / Flavors': FlavorAllView,
    'Clouds / Availability Zones': AvailabilityZoneAllView,
    'Clouds / Stacks': StackAllView,
}


@pytest.fixture(scope="module")
def visual(appliance):
    return Visual(appliance=appliance)


@pytest.fixture(scope='module', params=['10', '20', '50', '100', '200', '500', '1000'])
def value(request):
    return request.param


@pytest.fixture(scope='module', params=[CloudProvider,
                                        AvailabilityZone,
                                        'cloud_tenants',
                                        Flavor,
                                        Instance,
                                        'stacks',
                                        'keypairs'])
def page(request):
    return request.param


@pytest.yield_fixture(scope="module")
def set_grid(visual):
    gridlimit = visual.grid_view_limit
    yield
    visual.grid_view_limit = gridlimit


@pytest.yield_fixture(scope="module")
def set_tile(visual):
    tilelimit = visual.tile_view_limit
    yield
    visual.tile_view_limit = tilelimit


@pytest.yield_fixture(scope="module")
def set_list(visual):
    listlimit = visual.list_view_limit
    yield
    visual.list_view_limit = listlimit


def set_default_page(visual):
    visual.login_page = "Cloud Intel / Dashboard"


def go_to_grid(page):
    view = navigate_to(page, 'All')
    view.toolbar.view_selector.select('Grid View')


@pytest.yield_fixture(scope="module")
def set_cloud_provider_quad(visual):
    visual.cloud_provider_quad = False
    yield
    visual.cloud_provider_quad = True


def test_cloud_grid_page_per_item(visual, request, page, value, set_grid, appliance):
    """ Tests grid items per page

    Metadata:
        test_flag: visuals
    """
    if isinstance(page, six.string_types):
        page = getattr(appliance.collections, page)
    if visual.grid_view_limit != value:
        visual.grid_view_limit = int(value)
    request.addfinalizer(lambda: go_to_grid(page))
    limit = visual.grid_view_limit
    view = navigate_to(page, 'All', use_resetter=False)
    view.toolbar.view_selector.select("Grid View")
    max_item = view.entities.paginator.max_item
    item_amt = view.entities.paginator.items_amount
    if int(item_amt) >= int(limit):
        assert int(max_item) == int(limit), "Gridview Failed for page {}!".format(page)
    assert int(max_item) <= int(item_amt)


def test_cloud_tile_page_per_item(visual, request, page, value, set_tile, appliance):
    """ Tests tile items per page

    Metadata:
        test_flag: visuals
    """
    if isinstance(page, six.string_types):
        page = getattr(appliance.collections, page)
    if visual.tile_view_limit != value:
        visual.tile_view_limit = int(value)
    request.addfinalizer(lambda: go_to_grid(page))
    limit = visual.tile_view_limit
    view = navigate_to(page, 'All', use_resetter=False)
    view.toolbar.view_selector.select('Tile View')
    max_item = view.entities.paginator.max_item
    item_amt = view.entities.paginator.items_amount
    if int(item_amt) >= int(limit):
        assert int(max_item) == int(limit), "Tileview Failed for page {}!".format(page)
    assert int(max_item) <= int(item_amt)


def test_cloud_list_page_per_item(visual, request, page, value, set_list, appliance):
    """ Tests list items per page

    Metadata:
        test_flag: visuals
    """
    if isinstance(page, six.string_types):
        page = getattr(appliance.collections, page)
    if visual.list_view_limit != value:
        visual.list_view_limit = int(value)
    request.addfinalizer(lambda: go_to_grid(page))
    limit = visual.list_view_limit
    view = navigate_to(page, 'All', use_resetter=False)
    view.toolbar.view_selector.select('List View')
    max_item = view.entities.paginator.max_item
    item_amt = view.entities.paginator.items_amount
    if int(item_amt) >= int(limit):
        assert int(max_item) == int(limit), "Listview Failed for page {}!".format(page)
    assert int(max_item) <= int(item_amt)


@pytest.mark.parametrize('start_page', landing_pages, scope="module")
def test_cloud_start_page(visual, request, appliance, start_page):
    # TODO: Need to dynamically fetch this value and move this test case to common.
    """ Tests start page

    Metadata:
        test_flag: visuals
    """
    start = "" if appliance.version < '5.8' else "Compute / "
    new_start_page = "{}{}".format(start, start_page)
    request.addfinalizer(lambda: set_default_page(visual))
    visual.login_page = new_start_page
    appliance.server.logout()
    appliance.server.login_admin()
    landing_view = appliance.browser.create_view(landing_pages[start_page])
    assert landing_view.is_displayed


def test_cloudprovider_noquads(request, set_cloud_provider_quad):
    view = navigate_to(CloudProvider, 'All')
    view.toolbar.view_selector.select("Grid View")
    # Here data property will return an empty dict when the Quadrants option is deactivated.
    assert not view.entities.get_first_entity().data
