from django.utils.translation import gettext as _


class ROUTE_TYPE:
    data = [("P", "Pick-up"), ("D", "Drop-off")]
    default = data[0][0]

    @staticmethod
    def _filter_from_url(journey_type):
        """
        Thai: will refractor later to match with the url
        """
        if journey_type == 'pickup':
            return ROUTE_TYPE.data[0]
        elif journey_type == 'dropoff':
            return ROUTE_TYPE.data[1]
        else:
            None


STUDENT_STATUS = [
    (0, _('Not on bus yet')),
    (1, _('Missing')),
    (2, _('Absence with report')),
    (3, _('Student is on the way to school')),
    (4, _('Student is on the way to home')),
    (5, _('Student already reached school')),
    (6, _('Student already reached home')),
]

BUS_STATUS = (
    (0, _('On the way to pickup')),
    (1, _('Not yet started')),
    (2, _('On the way to home')),
)
