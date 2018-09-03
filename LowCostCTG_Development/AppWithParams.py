from kivy.app import App

class AppWithParams(App):

    params = {}

    @classmethod
    def getParamWithException(cls, k):
        """Returns param value if present, otherwise raise exception"""
        return cls.params[k]


    @classmethod
    def getParam(cls, k):
        """Returns param value if present, otherwise None"""
        try:
            return cls.params[k]
        except Exception:
            return None


    @classmethod
    def setParam(cls, k, v):
        cls.params[k] = v


    def getSetting(self, section, key, isFloat=False, isInt=False, isBoolean=False):
        """Get setting value from corresponding configuration section"""
        # app = self.get_running_app()
        setting = self.config.get(section, key)
        if isFloat:
            return float(setting)
        elif isInt:
            return int(setting)
        elif isBoolean:
            return setting == '1' or setting == 1 or setting == True
        else:
            return setting