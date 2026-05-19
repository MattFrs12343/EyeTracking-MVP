class StabilityFilter:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.current_confirmed_state = None
        self.last_raw_state = None
        self.hold_counter = 0

    def filter_state(self, raw_state):
        """
        Aplica filtro de estabilidad (holdframes).
        Retorna el estado confirmado si hay cambio, o None si no se confirma cambio.
        """
        holdframes = self.config_manager.get("holdframes", 4)

        if raw_state == self.last_raw_state:
            self.hold_counter += 1
        else:
            self.hold_counter = 1
            self.last_raw_state = raw_state

        if self.hold_counter >= holdframes:
            if raw_state != self.current_confirmed_state:
                self.current_confirmed_state = raw_state
                # Reiniciamos el contador opcionalmente tras un cambio confirmado
                # self.hold_counter = 0 
                return self.current_confirmed_state
        
        # Si no hay cambio confirmado, retorna None
        return None

    def get_current_state(self):
        return self.current_confirmed_state
