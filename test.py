
class A:
    def __init__(self, parent):
        self.key = 1
        self.parent = parent

class B:
    def __init__(self):
        obj = A('b')
        obj.key =  4
        o = A(obj)
        obj.key = 6
        print(o.parent.key)

b = B()