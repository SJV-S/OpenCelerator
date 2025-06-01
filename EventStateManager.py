from app_imports import *
import inspect  # Direct import to avoid circular dependency


class EventBus:
    _instance = None
    debug_init = False
    debug_subscribe = False
    debug_trigger = False
    debug_emit = False
    debug_refresh = False
    debug_all = False

    def __new__(cls):
        if cls._instance is None:
            if cls.debug_all or cls.debug_init:
                print("[DEBUG] Creating new EventBus instance")
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers = {}
            cls._instance.event_triggers = {}
            if cls.debug_all or cls.debug_init:
                print("[DEBUG] EventBus instance initialized with empty subscribers and triggers")
        return cls._instance

    def __init__(self):
        pass

    def subscribe(self, event, callback, has_data=False):
        if self.debug_all or self.debug_subscribe:
            print(f"[DEBUG] Adding subscription for event: {event}")

        if event not in self.subscribers:
            if self.debug_all or self.debug_subscribe:
                print(f"[DEBUG] Creating new subscriber list for event: {event}")
            self.subscribers[event] = []
        else:
            print(f"Event '{event}' already registered.")

        self.subscribers[event].append((callback, has_data))

        if self.debug_all or self.debug_subscribe:
            print(f"[DEBUG] Current subscribers for {event}: {len(self.subscribers[event])}")

    def add_event_trigger(self, source_event, target_event):
        if self.debug_all or self.debug_trigger:
            print(f"[DEBUG] Adding trigger: {source_event} -> {target_event}")
        self.event_triggers[source_event] = target_event
        if self.debug_all or self.debug_trigger:
            print(f"[DEBUG] Current triggers: {self.event_triggers}")

    def emit(self, event, data=None):
        result = None
        if self.debug_refresh and event == 'refresh_chart':
            print(f"[DEBUG] Emitting event: {event}")

        if event in self.subscribers:
            if self.debug_all or self.debug_emit:
                print(f"[DEBUG] Subscribers found: {event in self.subscribers}")
                print(f"[DEBUG] Trigger found: {event in self.event_triggers}")
                print(f"[DEBUG] Processing {len(self.subscribers[event])} subscribers")
            for callback, has_data in self.subscribers[event]:
                if self.debug_all or self.debug_emit:
                    print(f"[DEBUG] Executing callback: {callback.__name__}")
                if has_data:
                    result = callback(data)
                else:
                    result = callback()
        else:
            print(f'Subscribe event {event} not found.')

        if event in self.event_triggers:
            target_event = self.event_triggers[event]
            if self.debug_all or self.debug_emit:
                print(f"[DEBUG] Triggering chained event: {target_event}")
            self.emit(target_event)
        else:
            if self.debug_trigger:
                print(f'{event} does not tigger additional events.')

        return result


class StateRegistry:
    _instance = None
    debug_state_changes = False
    debug_state_access = False
    debug_state_access_fallback = False

    def __new__(cls, data_manager):
        if cls._instance is None:
            cls._instance = super(StateRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self, data_manager):
        # Classes
        self.event_bus = EventBus()
        self.data_manager = data_manager

        # Event bus subscriptions
        self.event_bus.subscribe("update_user_preference", self.update_user_pref, has_data=True)
        self.event_bus.subscribe("update_chart_data", self.update_chart_data, has_data=True)
        self.event_bus.subscribe("get_user_preference", self.get_user_pref, has_data=True)
        self.event_bus.subscribe("get_chart_data", self.get_chart_data, has_data=True)

    def _get_caller_info(self):
        # Get information about who is calling a state method
        # Go back three frames: current -> get_user_pref -> emit -> original caller
        frame = inspect.currentframe().f_back.f_back.f_back
        file_name = frame.f_code.co_filename.split('/')[-1]
        line_num = frame.f_lineno
        func_name = frame.f_code.co_name

        return f"[Caller: {file_name}:{line_num} in {func_name}()]"

    def update_user_pref(self, data):
        keys, value = data
        caller_info = self._get_caller_info()

        # Convert single key to list for consistent handling
        if not isinstance(keys, list):
            keys = [keys]

        if self.debug_state_changes:
            # Navigate to get the old value
            old_value = self.data_manager.user_preferences
            for i, key in enumerate(keys[:-1]):
                if key in old_value:
                    old_value = old_value[key]
                else:
                    old_value = "None"
                    break
            if isinstance(old_value, dict) and keys[-1] in old_value:
                old_value = old_value[keys[-1]]
            else:
                old_value = "None"

            print(
                f"[STATE CHANGE] {caller_info} User preference '{'.'.join(str(k) for k in keys)}' changing: {old_value} -> {value}")

        # Update the nested dictionary
        current = self.data_manager.user_preferences
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def update_chart_data(self, data):
        keys, value = data
        caller_info = self._get_caller_info()

        # Convert single key to list for consistent handling
        if not isinstance(keys, list):
            keys = [keys]

        if self.debug_state_changes:
            # Navigate to get the old value
            old_value = self.data_manager.chart_data
            for i, key in enumerate(keys[:-1]):
                if key in old_value:
                    old_value = old_value[key]
                else:
                    old_value = "None"
                    break
            if isinstance(old_value, dict) and keys[-1] in old_value:
                old_value_repr = str(old_value[keys[-1]])
            else:
                old_value_repr = "None"

            new_value_repr = str(value)

            if len(old_value_repr) > 100:
                old_value_repr = old_value_repr[:97] + "..."
            if len(new_value_repr) > 100:
                new_value_repr = new_value_repr[:97] + "..."

            print(f"[STATE CHANGE] {caller_info} Chart data '{'.'.join(str(k) for k in keys)}' changing:")
            print(f"  From: {old_value_repr}")
            print(f"  To:   {new_value_repr}")

        # Update the nested dictionary
        current = self.data_manager.chart_data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def get_user_pref(self, data):
        keys, fallback = data
        caller_info = self._get_caller_info()

        # Convert single key to list for consistent handling
        if not isinstance(keys, list):
            keys = [keys]

        # Navigate the nested dictionary
        value = self.data_manager.user_preferences
        key_exists = True

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                key_exists = False
                value = fallback
                break

        # Determine if we should log based on flags and conditions
        should_log = False
        log_message = ""

        # Case 1: Always log if debug_state_access is True
        if self.debug_state_access:
            should_log = True
            if key_exists:
                log_message = f"[STATE ACCESS] {caller_info} Reading user preference '{'.'.join(str(k) for k in keys)}' = {value}"
            else:
                log_message = f"[STATE ACCESS] {caller_info} Reading user preference '{'.'.join(str(k) for k in keys)}' = {value} (FALLBACK USED)"

        # Case 2: Log only fallbacks if debug_state_access_fallback is True and a fallback is used
        elif self.debug_state_access_fallback and not key_exists:
            should_log = True
            log_message = f"[STATE ACCESS] {caller_info} Reading user preference '{'.'.join(str(k) for k in keys)}' = {value} (FALLBACK USED)"

        if should_log:
            print(log_message)

        return value

    def get_chart_data(self, data):
        keys, fallback = data
        caller_info = self._get_caller_info()

        # Convert single key to list for consistent handling
        if not isinstance(keys, list):
            keys = [keys]

        # Navigate the nested dictionary
        value = self.data_manager.chart_data
        key_exists = True

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                key_exists = False
                value = fallback
                break

        value_repr = str(value)
        if len(value_repr) > 100:
            value_repr = value_repr[:97] + "..."

        # Determine if we should log based on flags and conditions
        should_log = False
        log_message = ""

        # Case 1: Always log if debug_state_access is True
        if self.debug_state_access:
            should_log = True
            if key_exists:
                log_message = f"[STATE ACCESS] {caller_info} Reading chart data '{'.'.join(str(k) for k in keys)}' = {value_repr}"
            else:
                log_message = f"[STATE ACCESS] {caller_info} Reading chart data '{'.'.join(str(k) for k in keys)}' = {value_repr} (FALLBACK USED)"

        # Case 2: Log only fallbacks if debug_state_access_fallback is True and a fallback is used
        elif self.debug_state_access_fallback and not key_exists:
            should_log = True
            log_message = f"[STATE ACCESS] {caller_info} Reading chart data '{'.'.join(str(k) for k in keys)}' = {value_repr} (FALLBACK USED)"

        if should_log:
            print(log_message)

        return value
