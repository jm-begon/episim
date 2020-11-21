from abc import ABCMeta


class VirusParameter(object, metaclass=ABCMeta):
    """
    Modeling virus parameter for respiratory-based infection (airborne + droplet)
    """
    @property
    def airborne_transmission_rate(self):
        return 0.5

    @property
    def droplet_transmission_rate(self):
        return 0.5

    @property
    def exposed_duration(self):
        return 1

    @property
    def infectious_duration(self):
        return 1

    @property
    def immunity_drop_rate(self):
        return 0

    @property
    def transmission_rate(self):
        # Discuss this
        return max(self.droplet_transmission_rate,
                   self.airborne_transmission_rate)



class VPDecorator(VirusParameter):
    def __init__(self, virus_parameter):
        self._virus_parameter = virus_parameter

    @property
    def airborne_transmission_rate(self):
        return self._virus_parameter.airborne_transmission_rate

    @property
    def droplet_transmission_rate(self):
        return self._virus_parameter.droplet_transmission_rate

    @property
    def exposed_duration(self):
        return self._virus_parameter.exposed_duration

    @property
    def infectious_duration(self):
        return self._virus_parameter.infectious_duration

    @property
    def immunity_drop_rate(self):
        return self._virus_parameter.immunity_drop_rate


class WearingMask(VPDecorator):
    def __init__(self, vp, airborne_protection_coefficient,
                 droplet_protection_coefficient):
        super().__init__(vp)
        self._airborne_coeff = airborne_protection_coefficient
        self._droplet_coeff = droplet_protection_coefficient

    @property
    def airborne_transmission_rate(self):
        return self._airborne_coeff * super().airborne_transmission_rate

    @property
    def droplet_transmission_rate(self):
        return self._droplet_coeff * super().droplet_transmission_rate


class Distancing(VPDecorator):
    @property
    def droplet_transmission_rate(self):
        # Guess. Could be refined with a pdf of droplet ejection distance
        return 0.0001 * super().droplet_transmission_rate


class Outing(VPDecorator):
    @property
    def airborne_transmission_rate(self):
        # Guess. How to do better ?
        return 0.0001 * super().airborne_transmission_rate






class PopulationParameter(object, metaclass=ABCMeta):
    """
    contact_frequency taken from [1] (high value, could be weighted and average
    with an age pyramid, did not read thoroughly, only interested in an
    approximation).

    [1] Del Valle, S. Y., Hyman, J. M., Hethcote, H. W., & Eubank, S. G. (2007). Mixing patterns between age groups in social networks. Social Networks, 29(4), 539-554.

    """
    @property
    def contact_frequency(self):
        return 20

class PopulationBehavior(PopulationParameter):
    def __init__(self, contact_frequency=20):
        self._contact_frequency = contact_frequency

    def __repr__(self):
        return "{}(contact_frequency={})" \
               "".format(self.__class__.__name__, self._contact_frequency)

    @property
    def contact_frequency(self):
        return self._contact_frequency



class InterventionDecorator(PopulationParameter):
    def __init__(self, population_parameter):
        self._population_parameter = population_parameter

    @property
    def contact_frequency(self):
        return self._population_parameter.contact_frequency


class Confine(InterventionDecorator):
    def __init__(self, population_parameter, efficiency):
        super().__init__(population_parameter)
        self._efficiency = efficiency

    def __repr__(self):
        return "{}({}, efficiency={})".format(self.__class__.__name__,
                                              repr(self._population_parameter),
                                              repr(self._efficiency))


    @property
    def contact_frequency(self):
        return (1-self._efficiency) * super().contact_frequency


