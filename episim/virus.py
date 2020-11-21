from .parameters import VirusParameter


class Virus(VirusParameter):
    def __init__(self, airborne_transmission_rate, droplet_transmisison_rate,
                 exposed_duration, infectious_duration,
                 immunity_drop_rate, name=None):
        self._airborne_tr = airborne_transmission_rate
        self._droplet_tr = droplet_transmisison_rate
        self._exposed_t = exposed_duration
        self._infectious_t = infectious_duration
        self._immunity_dr = immunity_drop_rate
        if name is None:
            name = self.__class__.__name__
        self._name = name

    def __repr__(self):
        return "{}(airborne_transmission_rate={}, " \
               "droplet_transmisison_rate={}, exposed_duration={}, " \
               "infectious_duration={}, immunity_drop_rate={}, name={})" \
               "".format(Virus.__name__,
                         repr(self._airborne_tr),
                         repr(self._droplet_tr),
                         repr(self._exposed_t),
                         repr(self._infectious_t),
                         repr(self._immunity_dr),
                         repr(self._name),
                         )

    def __str__(self):
        return "{}(airborne_transmission_rate={:.2e}, " \
               "droplet_transmisison_rate={:.2e}, exposed_duration={:.1f}, " \
               "infectious_duration={:.1f}, immunity_drop_rate={:.2e})" \
               "".format(Virus.__name__,
                         self._airborne_tr,
                         self._droplet_tr,
                         self._exposed_t,
                         self._infectious_t,
                         self._immunity_dr)

    @property
    def airborne_transmission_rate(self):
        return self._airborne_tr

    @property
    def droplet_transmission_rate(self):
        return self._droplet_tr

    @property
    def exposed_duration(self):
        return self._exposed_t

    @property
    def infectious_duration(self):
        return self._infectious_t

    @property
    def immunity_drop_rate(self):
        return self._immunity_dr


    def compute_total_n_infected(self, state_history):
        E = 0
        I = 0
        for state in state_history:
            E += state.exposed
            I += state.infected

        return .5 * (E / self.exposed_duration + I / self.infectious_duration)





class SARSCoV2Th(Virus):
    """
    Theoritical SARSCoV2 base on observation
    """
    def __init__(self):
        ## DURATIONS (those are averages/medians)
        # incubation is the time between contagion and first symptoms
        incubation_duration = 7   # [1]
        # infectious period starts a few days before symptoms
        exposed_duration = incubation_duration - 3  # [2]
        infectious_duration = 7  # [2]

        ## TRANSMISSION RATE (tr)
        R_0 = 3  # [3] quite debatable though
        contact_freq = 20  # [4]
        # R_0 = tr * contact_frequency * infectious_duration
        tr = R_0 / (contact_freq * infectious_duration)
        # in the absence of data, assumed to be the same for airbone and droplet
        airborne_tr = tr
        droplet_tr = tr

        # IMMUNITY DROP
        # Percentage who do not develops immunity
        p_no_immunity = 0.001  # pure guess
        # Percentage of people who lose immunity after 3 months  [5]
        p_lose_immunity = 0.15
        immunity_duration = 4.5 * 30  # 3 to 6 months x days
        immunity_drop_rate = p_no_immunity + p_lose_immunity / immunity_duration


        ## SOURCES
        # [1] https://fr.wikipedia.org/wiki/Maladie_%C3%A0_coronavirus_2019#Incubation 12/11/2020
        # [2] https://www.who.int/news-room/q-a-detail/q-a-how-is-covid-19-transmitted 12/11/2020
        # [3] https://en.wikipedia.org/wiki/Transmission_of_COVID-19#Reproduction_number 12/11/2020
        # [4] Del Valle, S. Y., Hyman, J. M., Hethcote, H. W., & Eubank, S. G. (2007). Mixing patterns between age groups in social networks. Social Networks, 29(4), 539-554.
        # [5] https://www.youtube.com/watch?v=OAYZr1WbePk ~ 20min. (TODO lookup better source)

        super().__init__(airborne_tr, droplet_tr, exposed_duration,
                         infectious_duration, immunity_drop_rate)
