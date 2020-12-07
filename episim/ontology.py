class Queryable(object):
    def __init__(self, ontology, state):
        self.ontology = ontology
        self.state = state

    def __getattr__(self, item):
        ans = getattr(self.state, item)
        if ans is None:
            ans = 0
            for name in self.ontology.children_names(item):
                ans += getattr(self, name)
        return ans


class WithShort(object):
    def __init__(self, name, short_name):
        self.name = name
        self.short_name = short_name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,
                                   repr(self.name), repr(self.short_name))

    def __str__(self):
        return str(self.name)


class Ontology(object):
    @classmethod
    def default_ontology(cls):
        return cls(
            {
                WithShort("population", "N"): {
                    WithShort("living", "L"): {
                        WithShort("susceptible", "S"): None,
                        WithShort("infected", "Id"): {
                            WithShort("exposed", "E"): None,
                            WithShort("infectious", "I"):{
                                WithShort("asymptomatic", "Ia"): None,
                                WithShort("presymptomatic", "Ip"): None,
                                WithShort("symptomatic", "Is"): None,
                            }

                        },
                        WithShort("recovered", "R"): None
                    },
                    WithShort("deceased", "D"): None
                    }
            }
        )

    def __init__(self, tree_dict):
        self.onto_tree = tree_dict
        self.entries = {}
        self.short_names = {}
        self._fill_entries(tree_dict)

    def _fill_entries(self, onto_node):
        if onto_node is None:
            return
        for key, value in onto_node.items():
            if isinstance(key, WithShort):
                self.shorten(key.name, key.short_name)
                key = key.name
            self.entries[key] = value
            self._fill_entries(value)

    def __call__(self, state):
        return Queryable(self, state)

    def children_names(self, s):
        d = self.entries.get(s)
        if d is not None:
            for k in d.keys():
                yield str(k)

    def shorten(self, long_name, short_name):
        self.short_names[long_name] = short_name

    def shortest_name(self, name):
        return self.short_names.get(name, name)









