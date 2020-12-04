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


class TransmissionRateMultiplier(VPDecorator):
    def __init__(self, virus_parameter, weight=1.):
        super().__init__(virus_parameter)
        self.weight = weight
    @property
    def transmission_rate(self):
        return self.weight * super().transmission_rate


class WearingMask(VPDecorator):
    # TODO source on mask efficiency
    """
    Efficiency
    ----------
    The probability `p_{i,j}` of a susceptible person `i` being infected by an
    infectious person `j` is supposed to be of the form

    .. math::
        p_{i,j} = F_{i,j}(A, D, X)

    where `A` is the quantity of breathed airborne molecules,
    `D` is the quantity of breathed droplet molecules,
    `X` represents all the other contamination method (which are believed
    to be much less important for SARS-CoV 2 [1]).

    The probability also depends on the viral load of `j` and of the immune
    system of `i`.

    The marginals should be monotonously increasing (if the input values of `F`
    are fixed except for one, increasing that value should increase the
    infection probability).

    A mask works by filtering `A` and `D`. If the mask offers an airborne
    out-protection of `u` and a droplet out-protection of `q` and person `j`
    emits `A` and `D`, the mask will let pass only

    ..math::
        A' = (1-u) A
        D' = (1-q) D


    The mask also offers a protection to the wearer, although to a lesser
    extent (harder to get data on this). If the mask offers an airborne
    in-protection of `v` and a droplet in-protection of `r`, person `i`
    is only exposed to

    ..math::
        A' = (1-v) A
        D' = (1-r) D

    of what is emitted by `j` (possibly already filtered by `j`'s mask).

    Other factors come into play. Not all masks offer the same protection.
    Other factors also governs `F_{i, j}` (e.g. indoor vs. outdoor for airborne,
    physical distance for droplet).
    The protection only applies when at least one party is wearing the mask.
    The probability of wearing a mask might not be uniform in the general
    population (clusters of non-wearers who interact more among them).
    The probability of being infectious might also depends on mask habits.
    The mask efficiency might not be constant with respect to time, etc.

    The `VirusParameter` class relies on the following model

    ..math::
        p_{i, j} = p = max(p_A, p_D)


    Given average efficiencies w and s (accounting for u, q, v, r and the
    probability of each party wearing a mask), we will make the following linear
    assuptiom

    ..math::
        p' = max((1-w) p_A, (1-s) p_D)


    Sources
    -------
    [1] https://www.youtube.com/watch?v=OAYZr1WbePk


    Default values
    --------------
    Assumptions to compute the average protection

     - x % of people wearing mask
     - Uniformity and independence

    ..math::
        1-w =  (1-x) \times (1-x) 1 + (1-x) \times x \times (1-u)
             + x \times (1-x) (1-v) + x \times x (1-v)(1-u)


    We will use the following default values:

     - x = .75
     - u = .8, q = .9
     - v = .3, r = .7


    """
    @classmethod
    def compute_protection(cls, p_wear, prot_i, prot_s):
        # x is the risk
        x = 0
        # Nobody wears mask
        x += (1-p_wear)**2 * 1
        # Only infectious wears mask
        x += (1-p_wear)*p_wear * (1-prot_i)
        # Only susceptible wears mask
        x += p_wear*(1-p_wear) * (1-prot_s)
        # Both wear mask
        x += p_wear**2 * (1-prot_i) * (1-prot_s)

        return 1 - x


    def __init__(self, vp, airborne_protection=.69,
                 droplet_protection=.85):
        super().__init__(vp)
        self._airborne_coeff = 1-airborne_protection
        self._droplet_coeff = 1-droplet_protection

    @property
    def airborne_transmission_rate(self):
        return self._airborne_coeff * super().airborne_transmission_rate

    @property
    def droplet_transmission_rate(self):
        return self._droplet_coeff * super().droplet_transmission_rate

    def __repr__(self):
        return "{}({}, airborne_protection={}, droplet_protection={})" \
               "".format(self.__class__.__name__,
                         repr(self._virus_parameter),
                         repr(1-self._airborne_coeff),
                         repr(1-self._droplet_coeff))

    def __str__(self):
        return "{}({}, airborne_protec.={:.2f}, droplet_protec.={:.2f})" \
               "".format(self.__class__.__name__,
                         str(self._virus_parameter),
                         1-self._airborne_coeff,
                         1-self._droplet_coeff)



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


