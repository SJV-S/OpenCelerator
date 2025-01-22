class EventBus:
    _instance = None
    debug_init = False
    debug_subscribe = False
    debug_trigger = False
    debug_emit = False
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
        if self.debug_all or self.debug_emit:
            print(f"[DEBUG] Emitting event: {event}")
            print(f"[DEBUG] Event data: {data}")
            print(f"[DEBUG] Subscribers found: {event in self.subscribers}")
            print(f"[DEBUG] Trigger found: {event in self.event_triggers}")

        if event in self.subscribers:
            if self.debug_all or self.debug_emit:
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
