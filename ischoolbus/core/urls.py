from django.urls import path
from .views import BusInfoSupervisorView, StartJourneyView, \
        ParentListView, BusView, NextStopView, get_students_for_parent, \
        get_student_estimation_for_parent, \
        StudentCrudView, BusSupervisorView, DriverView, save_bus_route_view, \
        get_route_locations_view, get_parent_by_id_number_view, get_routes_by_type_view, \
        RouteView, BusLocationView, assign_student_to_route_view, query_students_from_route_view, confirm_to_school, \
        confirm_to_bus, query_attendances_for_bus_route_view, set_absence, update_status_at_location, query_moving_route_view, \
        send_notification_to_parents_view, send_delay, get_routes_by_bus_view, get_routes_by_driver_view, \
        get_routes_by_bus_supervisor_view, get_routes_of_student, finish_journey, update_bus_route_with_location_view,  \
        NotificationTemplateView, query_server_settings, query_log_messages, query_route_info_by_student_view,  \
        query_absence_by_student_view, get_contacts_for_student, ContactView, delete_absence_of_student_view

urlpatterns = [
    # student api
    path('api/student/<int:student_id>/contacts/',
         get_contacts_for_student,
         name='get_contacts_for_student'),
    path('api/student/absence/', set_absence, name='set_absence'),
    path('api/student/update-status-at-location/',
         update_status_at_location,
         name='update_status_at_location'),
    path('api/student', StudentCrudView.as_view(), name='StudentCrudView'),
    path('api/student/bus-route',
         assign_student_to_route_view,
         name="assign_student_to_route_view"),
    path('api/student/<int:pk>',
         StudentCrudView.as_view(),
         name='StudentCrudView'),
    # parent api
    path('api/parent/absence/student/<int:student>/delete',
         delete_absence_of_student_view,
         name='delete_absence_of_student_view'),
    path('api/parent/absence/student/<int:student>',
         query_absence_by_student_view,
         name='query_absence_by_student_view'),
    path('api/parent/student/route',
         query_route_info_by_student_view,
         name='query_route_info_by_student_view'),
    path('api/parent/student/<int:student_id>/<int:route_id>',
         get_student_estimation_for_parent,
         name='get_student_estimation_for_parent'),
    path('api/parent/students',
         get_students_for_parent,
         name='get_students_for_parent'),
    path('api/parent/notify',
         send_notification_to_parents_view,
         name="send_notification_to_parents_view"),
    path('api/parent', ParentListView.as_view(), name='ParentListView'),
    path('api/parent/<int:pk>', ParentListView.as_view(), name='ParentView'),
    path('api/parent/by-id-number/<str:id_number>',
         get_parent_by_id_number_view,
         name='Get Parent by id number'),
    # supervisor api
    path('api/supervisor/bus/detail',
         BusInfoSupervisorView.as_view(),
         name='BusInfoSupervisorView'),
    path('api/supervisor/bus/start/<journey_type>',
         StartJourneyView.as_view(),
         name='StartJourneyView'),
    path('api/supervisor',
         BusSupervisorView.as_view(),
         name="BusSupervisorView"),
    path('api/supervisor/<int:pk>',
         BusSupervisorView.as_view(),
         name="BusSupervisorView"),
    path('api/supervisor/bus/confirm-to-school',
         confirm_to_school,
         name="confirm_to_school"),
    path('api/supervisor/bus/confirm-to-bus',
         confirm_to_bus,
         name="confirm_to_bus"),
    path('api/supervisor/<int:bus_supervisor_id>/bus_routes',
         get_routes_by_bus_supervisor_view,
         name="get_routes_by_bus_supervisor_view"),
    # bus api
    path('api/bus', BusView.as_view(), name="BusView"),
    path('api/bus/<int:pk>', BusView.as_view(), name="BusView"),
    path('api/bus/nextstop/<int:location_id>',
         NextStopView.as_view(),
         name="NextStopView"),
    path('api/bus/<int:bus_id>/bus_routes',
         get_routes_by_bus_view,
         name="get_routes_by_bus_view"),

    # contact
    path('api/contacts', ContactView.as_view(), name="ContactView"),
    path('api/contacts/<int:pk>', ContactView.as_view(), name="ContactView"),

    # dirver
    path('api/driver', DriverView.as_view(), name="DriverView"),
    path('api/driver/<int:pk>', DriverView.as_view(), name="DriverView"),
    path('api/driver/<int:driver_id>/bus_routes',
         get_routes_by_driver_view,
         name="get_routes_by_driver_view"),

    # bus route api
    path('api/bus-route', RouteView.as_view(), name="BusRoute view"),
    path('api/bus-route/moving',
         query_moving_route_view,
         name="query_moving_route_view"),
    path('api/bus-route/<int:route>/students',
         query_students_from_route_view,
         name="query_students_from_route_view"),
    path('api/bus-route/<int:pk>', RouteView.as_view(), name="RouteView"),
    #     path('api/bus-route', save_bus_route_view, name="save_bus_route"),
    path('api/bus-route/by-type/<str:route_type>',
         get_routes_by_type_view,
         name="get_routes_by_type_view"),
    path('api/bus-route/<int:pk>/locations',
         get_route_locations_view,
         name="get_route_locations_view"),
    path('api/bus-route/student/<int:student_id>',
         get_routes_of_student,
         name="get_route_of_student"),
    path('api/bus_route/<int:route>/attendances',
         query_attendances_for_bus_route_view,
         name="query_attendances_for_bus_route_view"),
    path('api/bus_route/delay', send_delay, name="send_delay"),
    path('api/bus-route/finish/<int:route>',
         finish_journey,
         name="finish_journey"),
    # bus location
    path('api/bus-location', BusLocationView.as_view(),
         name="BusLocationView"),
    path('api/bus-location/<int:pk>',
         BusLocationView.as_view(),
         name="BusLocationView"),
    path('api/bus-route-location/<int:pk>',
         update_bus_route_with_location_view,
         name="update_bus_route_with_location_view"),

    # settings
    path('api/settings/notification-template',
         NotificationTemplateView.as_view(),
         name="NotificationTemplateView"),
    path('api/server', query_server_settings, name="query_server_settings"),
    path('api/log/messages', query_log_messages, name="query_log_messages"),
]
