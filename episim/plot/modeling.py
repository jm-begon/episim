"""
S = Variable("S", 0)
E = Variable("E", 1)
I = Variable("I", 2)
R = Variable("R", 3)
N = S + E + I + R
beta = Constant(.2, "beta")
gamma = Constant(.3, "gamma")
kappa = Constant(.1, "kappa")
ksi = Constant(.05, "ksi")
dS_dt = -beta*S*(0.1*E+I*0.8)/N + ksi*R
N.override_name("N")
print(dS_dt)

"""

class Node(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, *args):
        return 0

    def __add__(self, other):
        # self is left operand
        if not isinstance(other, Node):
            other = Constant(other)

        operands = []
        for node in self, other:
            if isinstance(node, Addition):
                operands.extend(node.operands)
            else:
                operands.append(node)
        return Addition.create(*operands)

    def __radd__(self, other):
        if not isinstance(other, Node):
            other = Constant(other)
            return other.__add__(self)
        return self.__add__(other)

    def __mul__(self, other):
        # self is left operand
        if not isinstance(other, Node):
            other = Constant(other)

        operands = []
        for node in self, other:
            if isinstance(node, Multiplication):
                operands.extend(node.operands)
            else:
                operands.append(node)
        return Multiplication.create(*operands)

    def __rmul__(self, other):
        if not isinstance(other, Node):
            other = Constant(other)
            return other.__mul__(self)
        return self.__mul__(other)


    def __neg__(self):
        return Minus.create(self)

    def __sub__(self, other):
        if not isinstance(other, Node):
            other = Constant(other)
        return self.__add__(Minus.create(other))


    def __truediv__(self, other):
        if not isinstance(other, Node):
            other = Constant(other)

        return Division.create(self, other)

    def __rtruediv__(self, other):
        if not isinstance(other, Node):
            other = Constant(other)
        return Division.create(other, self)


    def __str__(self):
        if self.name is None:
            return super().__str__()
        return str(self.name)




class Leaf(Node):
    pass


class Variable(Leaf):
    def __init__(self, name, index):
        super().__init__(name)
        self.index = index

    def __call__(self, *args):
        return args[self.index]

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,
                                   repr(self.name),
                                   repr(self.index))


class Constant(Leaf):
    def __init__(self, value, name=None, format="{:.2E}"):
        super().__init__(format.format(value) if name is None else name)
        self.value = value

    def __call__(self, *args):
        return self.value


    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,
                                   repr(self.value),
                                   repr(self.name))



class Function(Node):
    def __init__(self, name=None):
        super().__init__(name)

    def override_name(self, name):
        self.name = name
        return self

    def __str__(self):
        if self.name is not None:
            return super().__str__()
        return self.symbolic_repr()

    def symbolic_repr(self):
        return "n/a"


class Addition(Function):
    @classmethod
    def create(cls, *operands):
        if len(operands) == 0:
            return Constant(0)
        if len(operands) == 1 and isinstance(operands[0], Node):
            return operands[0]
        return cls(*operands)

    def __init__(self, *operands):
        super().__init__()
        self.operands = list(operands)

    def __call__(self, *args):
        s = 0
        for operand in self.operands:
            s += operand(*args)

        return s

    def symbolic_repr(self):
        s = " + ".join(str(x) for x in self.operands)
        s = s.replace("+ -", "- ")
        return s


    def __repr__(self):
        return "{}(*{})".format(self.__class__.__name__, repr(self.operands))


class Multiplication(Function):
    @classmethod
    def create(cls, *operands):
        if len(operands) == 0:
            return Constant(1)
        if len(operands) == 1 and isinstance(operands[0], Node):
            return operands[0]
        # Regroup minus
        n_minus = 0
        ls = []
        for operand in operands:
            if isinstance(operand, Minus):
                n_minus += 1
                operand = operand.operand
            ls.append(operand)
        operands = ls
        node = cls(*operands)
        if n_minus % 2 == 1:
            node = Minus(node)
        return node

    def __init__(self, *operands):
        super().__init__()
        self.operands = operands

    def __call__(self, *args):
        v = 1
        for operand in self.operands:
            v *= operand(*args)

        return v

    def symbolic_repr(self):
        ss = []
        for operand in self.operands:
            op_str = str(operand)
            if not isinstance(operand, Multiplication) and not isinstance(operand, Leaf):
                op_str = "({})".format(op_str)
            ss.append(op_str)

        return " ".join(ss)

    def __repr__(self):
        return "{}(*{})".format(self.__class__.__name__, repr(self.operands))

class Minus(Function):
    @classmethod
    def create(cls, operand):
        if isinstance(operand, Minus):
            return operand.operand
        return cls(operand)


    def __init__(self, operand):
        super().__init__()
        self.operand = operand

    def __call__(self, *args):
        return - self.operand(*args)

    def symbolic_repr(self):

        if isinstance(self.operand, Addition):
            return "-({})".format(self.operand)
        return "-{}".format(str(self.operand))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, repr(self.operand))


class Division(Function):
    @classmethod
    def create(cls, op1, op2):
        return cls(op1, op2)

    def __init__(self, op1, op2):
        super().__init__()
        self.op1 = op1
        self.op2 = op2

    def __call__(self, *args):
        return self.op1(*args) / self.op2(*args)

    def symbolic_repr(self):
        s1 = str(self.op1)
        if isinstance(self.op1, Addition) and ("+" in s1 or "-" in s1):
            s1 = "({})".format(s1)

        s2 = str(self.op2)
        if isinstance(self.op2, Addition) and ("+" in s2 or "-" in s2):
            s2 = "({})".format(s2)

        return "{}/{}".format(s1, s2)

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__,
                                   repr(self.op1),
                                   repr(self.op2))



class Accumulator(Node):
    def __init__(self, node, scale=1.):
        super().__init__(None)
        self.node = node
        self.memory = 0
        self.scale = scale

    def __call__(self, *x):
        y = self.node(*x)
        self.memory += y
        return y

    @property
    def value(self):
        return self.memory * self.scale

    def reset(self):
        self.memory = 0

    def __str__(self):
        return str(self.node)

    def __repr__(self):
        return "{}({}, {})" \
               "".format(self.__class__.__name__,
                         repr(self.node),
                         repr(self.scale))





class System(object):
    @classmethod
    def new(cls, *names):
        return iter(cls(*names))

    def __init__(self, *names):
        self.variables = [Variable(name, i) for i, name in enumerate(names)]

    def new_variables(self, *names):
        d = len(self.variables)
        self.variables.extend(Variable(name, i+d) for i, name in enumerate(names))


    def __iter__(self):
        return iter(self.variables)
