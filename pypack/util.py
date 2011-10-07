

def cached_property(f):
    """
    Decorator for a lazy-loaded object @property
    ...why is this not in the Python standard library?
    """
    def get(self):
        try:
            return self.__property_cache[f]
        except AttributeError:
            self.__property_cache = {}
        except KeyError:
            pass
        value = self.__property_cache[f] = f(self)
        return value

    return property(get)
