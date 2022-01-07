# -*- coding: utf-8 -*-

from abc import ABC
from collections import defaultdict, OrderedDict
from threading import Lock
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import Literal


class PyeeException(Exception):
    """An exception internal to pyee."""


class PyeeError(PyeeException):
    """An error internal to pyee."""


Event = TypeVar(name="Event", contravariant=True)
ErrorEvent = Literal["error"]
NewListenerEvent = Literal["new_listener"]

Arg = TypeVar(name="Arg", contravariant=True)
Kwarg = TypeVar(name="Kwarg", contravariant=True)


class HandlerP(Protocol[Arg, Kwarg]):
    def __call__(
        self,
        *args: Arg,
        **kwargs: Kwarg,
    ) -> Any:
        ...


DArg = TypeVar(name="DArg", covariant=True)
DKwarg = TypeVar(name="DKwarg", covariant=True)

DHandler = HandlerP[DArg, DKwarg]


TEvent = TypeVar(name="TEvent", contravariant=True)
TError = TypeVar(name="TError")
TArg = TypeVar(name="TArg")
TKwarg = TypeVar(name="TKwarg")
TErrorEvent = TypeVar(name="TErrorEvent")


class Entry(ABC, Generic[TArg, TKwarg]):
    def get_handler(self) -> HandlerP[TArg, TKwarg]:
        ...


class UserEntry(Entry[TArg, TKwarg]):
    pass


class ErrorEntry(Entry[TError, None]):
    pass


TUserHandler = HandlerP[TArg, TKwarg]
TErrorHandler = HandlerP[TError, None]


class NewListenerEntry(
    Generic[TEvent, TErrorEvent, TError, TArg, TKwarg],
    Entry[Union[TEvent, TErrorEvent, TUserHandler, TErrorHandler], None],
):
    pass


TNewListenerHandler = HandlerP[
    Union[TEvent, TErrorEvent, TUserHandler, TErrorHandler], None
]

THandler = Union[TUserHandler, TErrorHandler, TNewListenerHandler]

TEntry = Union[Entry[TArg, TKwarg], ErrorEntry, NewListenerEntry]


class Table(Generic[TEvent, TErrorEvent, TError, TArg, TKwarg]):
    def __init__(self):
        self.handlers: Dict[
            Union[TEvent, TErrorEvent, NewListenerEvent],
            "OrderedDict[THandler, TEntry]",
        ]

    def get_user_event_handler(self, event: TEvent, key: TUserHandler) -> TUserHandler:
        entry: TEntry = self.handlers[event][key]
        if isinstance(entry, UserEntry):
            return entry.get_handler()
        raise PyeeError(f"Unexpected handler: {entry.get_handler()}")

    def get_error_handler(
        self, event: TErrorEvent, key: TErrorHandler
    ) -> TErrorHandler:
        entry: TEntry = self.handlers[event][key]
        if isinstance(entry, ErrorEntry):
            return entry.get_handler()
        raise PyeeError(f"Unexpected handler: {entry.get_handler()}")

    def get_new_listener_handler(self, key: TNewListenerHandler) -> TNewListenerHandler:
        entry: TEntry = self.handlers["new_listener"][key]
        if isinstance(entry, NewListenerEntry):
            return entry.get_handler()
        raise PyeeError(f"Unexpected handler: {entry.get_handler()}")


AEvent = TypeVar(name="AEvent", contravariant=True)
AError = TypeVar(name="AError", contravariant=True)
AErrorEvent = TypeVar(name="AErrorEvent", contravariant=True)
AArg = TypeVar(name="AArg", contravariant=True)
AKwarg = TypeVar(name="AKwarg", contravariant=True)

AUserHandler = HandlerP[AArg, AKwarg]
AErrorHandler = HandlerP[AError, None]
ANewListenerHandler = HandlerP[
    Union[AEvent, AErrorEvent, AUserHandler, AErrorHandler], None
]

AHandler = Union[AUserHandler, AErrorHandler, ANewListenerHandler]

ADecorator = Callable[
    [
        HandlerP[
            Union[AArg, AEvent, AErrorEvent, AError, AUserHandler, AErrorHandler],
            AKwarg,
        ]
    ],
    HandlerP[
        Union[AArg, AEvent, AErrorEvent, AError, AUserHandler, AErrorHandler], AKwarg
    ],
]

AEntry = Union[Entry[AArg, AKwarg], ErrorEntry, NewListenerEntry]


class AbstractEventEmitter(Generic[AEvent, AErrorEvent, AError, AArg, AKwarg]):
    def __init__(self) -> None:
        self._table: Table[AEvent, AErrorEvent, AError, AArg, AKwarg] = Table()
        self._lock: Lock = Lock()

    def on(
        self,
        event: Union[AEvent, AErrorEvent, NewListenerEvent],
        f: Optional[
            Union[
                HandlerP[AArg, AKwarg],
                HandlerP[AError, None],
                HandlerP[
                    Union[
                        AArg,
                        AEvent,
                        AErrorEvent,
                        NewListenerEvent,
                        AError,
                        HandlerP[AArg, AKwarg],
                        HandlerP[AError, None],
                    ],
                    None,
                ],
            ]
        ] = None,
    ) -> Union[
        HandlerP[AArg, AKwarg],
        HandlerP[AError, None],
        HandlerP[
            Union[
                AArg,
                AEvent,
                AErrorEvent,
                NewListenerEvent,
                AError,
                HandlerP[AArg, AKwarg],
                HandlerP[AError, None],
            ],
            None,
        ],
        Callable[
            [
                HandlerP[
                    Union[
                        AArg,
                        AEvent,
                        AErrorEvent,
                        NewListenerEvent,
                        AError,
                        AUserHandler,
                        AErrorHandler,
                    ],
                    Optional[AKwarg],
                ]
            ],
            HandlerP[
                Union[
                    AArg,
                    AEvent,
                    AErrorEvent,
                    NewListenerEvent,
                    AError,
                    AUserHandler,
                    AErrorHandler,
                ],
                Optional[AKwarg],
            ],
        ],
    ]:
        if f is None:
            return self.listens_to(event)
        else:
            return self.add_listener(event, f)

    def listens_to(
        self, event: Union[AEvent, AErrorEvent, NewListenerEvent]
    ) -> Callable[
        [
            HandlerP[
                Union[
                    AArg,
                    AEvent,
                    AErrorEvent,
                    NewListenerEvent,
                    AError,
                    AUserHandler,
                    AErrorHandler,
                ],
                Optional[AKwarg],
            ]
        ],
        HandlerP[
            Union[
                AArg,
                AEvent,
                AErrorEvent,
                NewListenerEvent,
                AError,
                AUserHandler,
                AErrorHandler,
            ],
            Optional[AKwarg],
        ],
    ]:
        def on(
            f: HandlerP[
                Union[
                    AArg,
                    AEvent,
                    AErrorEvent,
                    NewListenerEvent,
                    AError,
                    HandlerP[AArg, AKwarg],
                    HandlerP[AError, None],
                ],
                Optional[AKwarg],
            ]
        ) -> HandlerP[
            Union[
                AArg,
                AEvent,
                AErrorEvent,
                NewListenerEvent,
                AError,
                HandlerP[AArg, AKwarg],
                HandlerP[AError, None],
            ],
            Optional[AKwarg],
        ]:
            return self.add_listener(event, f)

        return on

    def add_listener(
        self,
        event: Union[AEvent, AErrorEvent, NewListenerEvent],
        f: HandlerP[
            Union[
                AArg,
                AEvent,
                AErrorEvent,
                NewListenerEvent,
                AError,
                HandlerP[AArg, AKwarg],
                HandlerP[AError, None],
            ],
            Optional[AKwarg],
        ],
    ) -> HandlerP[
        Union[
            AArg,
            AEvent,
            AErrorEvent,
            NewListenerEvent,
            AError,
            HandlerP[AArg, AKwarg],
            HandlerP[AError, None],
        ],
        Optional[AKwarg],
    ]:
        self._add_event_handler(event, f, f)
        return f

    def _add_event_handler(
        self,
        event: Union[AEvent, AErrorEvent, NewListenerEvent],
        k: AHandler,
        v: AHandler,
    ):
        # Fire 'new_listener' *before* adding the new listener!
        self.emit("new_listener", event, k)

        # Add the necessary function
        # Note that k and v are the same for `on` handlers, but
        # different for `once` handlers, where v is a wrapped version
        # of k which removes itself before calling k
        with self._lock:
            self._events[event][k] = v

    def _emit_run(
        self,
        f: HandlerP[Event, Arg, Kwarg],
        args: Tuple[
            Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
            ...,
        ],
        kwargs: Dict[str, Kwarg],
    ) -> None:
        f(*args, **kwargs)

    def _emit_handle_potential_error(
        self,
        event: Union[Event, InternalEvent],
        error: Optional[Union[Arg, Exception, Event, InternalEvent, AnyHandlerP]],
    ) -> None:
        if event == "error":
            if isinstance(error, Exception):
                raise error
            else:
                raise PyeeError(f"Uncaught, unspecified 'error' event: {error}")

    def _call_handlers(
        self,
        event: Union[Event, InternalEvent],
        args: Tuple[
            Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
            ...,
        ],
        kwargs: Dict[str, Kwarg],
    ) -> bool:
        handled = False

        with self._lock:
            funcs = list(self._events[event].values())
        for f in funcs:
            self._emit_run(f, args, kwargs)
            handled = True

        return handled

    def emit(
        self,
        event: Union[Event, InternalEvent],
        *args: Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
        **kwargs: Kwarg,
    ) -> bool:
        """Emit ``event``, passing ``*args`` and ``**kwargs`` to each attached
        function. Returns ``True`` if any functions are attached to ``event``;
        otherwise returns ``False``.

        Example::

            ee.emit('data', '00101001')

        Assuming ``data`` is an attached function, this will call
        ``data('00101001')'``.
        """
        handled = self._call_handlers(event, args, kwargs)

        if not handled:
            self._emit_handle_potential_error(event, args[0] if args else None)

        return handled

    def once(
        self,
        event: Union[Event, InternalEvent],
        f: Optional[HandlerP[Event, Arg, Kwarg]] = None,
    ) -> Union[HandlerP[Event, Arg, Kwarg], DecoratorP[Event, Arg, Kwarg]]:
        """The same as ``ee.on``, except that the listener is automatically
        removed after being called.
        """

        def _wrapper(f: AnyHandlerP) -> AnyHandlerP:
            def g(
                *args: Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
                **kwargs: Kwarg,
            ) -> Any:
                with self._lock:
                    # Check that the event wasn't removed already right
                    # before the lock
                    if event in self._events and f in self._events[event]:
                        self._remove_listener(event, f)
                    else:
                        return None
                # f may return a coroutine, so we need to return that
                # result here so that emit can schedule it
                return f(*args, **kwargs)

            self._add_event_handler(event, f, g)
            return f

        if f is None:
            return _wrapper
        else:
            return _wrapper(f)

    def _remove_listener(
        self, event: Union[Event, InternalEvent], f: HandlerP[Event, Arg, Kwarg]
    ) -> None:
        """Naked unprotected removal."""
        self._events[event].pop(f)

    def remove_listener(
        self, event: Union[Event, InternalEvent], f: HandlerP[Event, Arg, Kwarg]
    ) -> None:
        """Removes the function ``f`` from ``event``."""
        with self._lock:
            self._remove_listener(event, f)

    def remove_all_listeners(
        self, event: Optional[Union[Event, InternalEvent]] = None
    ) -> None:
        """Remove all listeners attached to ``event``.
        If ``event`` is ``None``, remove all listeners on all events.
        """
        with self._lock:
            if event is not None:
                self._events[event] = OrderedDict()
            else:
                self._events = defaultdict(OrderedDict)

    def listeners(
        self, event: Union[Event, InternalEvent]
    ) -> List[HandlerP[Event, Arg, Kwarg]]:
        """Returns a list of all listeners registered to the ``event``."""
        return list(self._events[event].keys())


class EventEmitter(Generic[Event, Arg, Kwarg]):
    """The base event emitter class. All other event emitters inherit from
    this class.

    Most events are registered with an emitter via the ``on`` and ``once``
    methods, and fired with the ``emit`` method. However, pyee event emitters
    have two *special* events:

    - ``new_listener``: Fires whenever a new listener is created. Listeners for
      this event do not fire upon their own creation.

    - ``error``: When emitted raises an Exception by default, behavior can be
      overridden by attaching callback to the event.

      For example::

          @ee.on('error')
          def on_error(message):
              logging.err(message)

          ee.emit('error', Exception('something blew up'))

    All callbacks are handled in a synchronous, blocking manner. As in node.js,
    raised exceptions are not automatically handled for you---you must catch
    your own exceptions, and treat them accordingly.
    """

    def __init__(self) -> None:
        self._table: Table[Event, Arg, Kwarg] = Table()
        self._lock: Lock = Lock()

    def on(
        self,
        event: Union[Event, ErrorEvent, NewListenerEvent],
        f: Optional[HandlerP[Event, Arg, Kwarg]] = None,
    ) -> Union[HandlerP[Event, Arg, Kwarg], DecoratorP]:
        """Registers the function ``f`` to the event name ``event``, if provided.

        If ``f`` isn't provided, this method calls ``EventEmitter#listens_to`, and
        otherwise calls ``EventEmitter#add_listener``. In other words, you may either
        use it as a decorator::

            @ee.on('data')
            def data_handler(data):
                print(data)

        Or directly::

            ee.on('data', data_handler)

        In both the decorated and undecorated forms, the event handler is
        returned. The upshot of this is that you can call decorated handlers
        directly, as well as use them in remove_listener calls.

        Note that this method's return type is a union type. If you are using
        mypy or pyright, you will probably want to use either
        ``EventEmitter#listens_to`` or ``EventEmitter#add_listener``.
        """
        if f is None:
            return self.listens_to(event)
        else:
            return self.add_listener(event, f)

    def listens_to(
        self, event: Union[Event, InternalEvent]
    ) -> DecoratorP[Event, Arg, Kwarg]:
        """Returns a decorator which will register the decorated function to
        the event name ``event``. Usage::

            @ee.listens_to("event")
            def data_handler(data):
                print(data)

        By only supporting the decorator use case, this method has improved
        type safety over ``EventEmitter#on``.
        """

        def on(f: HandlerP[Event, Arg, Kwarg]) -> HandlerP[Event, Arg, Kwarg]:
            self._add_event_handler(event, f, f)
            return f

        return on

    def add_listener(
        self, event: Union[Event, InternalEvent], f: HandlerP[Event, Arg, Kwarg]
    ) -> HandlerP[Event, Arg, Kwarg]:
        """Register the function ``f`` to the event name ``event``. By only
        supporting non-decorator use cases, this method has improved type
        safety over ``EventEmitter#on``.
        """
        self._add_event_handler(event, f, f)
        return f

    def _add_event_handler(
        self,
        event: Union[Event, InternalEvent],
        k: HandlerP[Event, Arg, Kwarg],
        v: AnyHandlerP,
    ):
        # Fire 'new_listener' *before* adding the new listener!
        self.emit("new_listener", event, k)

        # Add the necessary function
        # Note that k and v are the same for `on` handlers, but
        # different for `once` handlers, where v is a wrapped version
        # of k which removes itself before calling k
        with self._lock:
            self._events[event][k] = v

    def _emit_run(
        self,
        f: HandlerP[Event, Arg, Kwarg],
        args: Tuple[
            Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
            ...,
        ],
        kwargs: Dict[str, Kwarg],
    ) -> None:
        f(*args, **kwargs)

    def _emit_handle_potential_error(
        self,
        event: Union[Event, InternalEvent],
        error: Optional[Union[Arg, Exception, Event, InternalEvent, AnyHandlerP]],
    ) -> None:
        if event == "error":
            if isinstance(error, Exception):
                raise error
            else:
                raise PyeeError(f"Uncaught, unspecified 'error' event: {error}")

    def _call_handlers(
        self,
        event: Union[Event, InternalEvent],
        args: Tuple[
            Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
            ...,
        ],
        kwargs: Dict[str, Kwarg],
    ) -> bool:
        handled = False

        with self._lock:
            funcs = list(self._events[event].values())
        for f in funcs:
            self._emit_run(f, args, kwargs)
            handled = True

        return handled

    def emit(
        self,
        event: Union[Event, InternalEvent],
        *args: Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
        **kwargs: Kwarg,
    ) -> bool:
        """Emit ``event``, passing ``*args`` and ``**kwargs`` to each attached
        function. Returns ``True`` if any functions are attached to ``event``;
        otherwise returns ``False``.

        Example::

            ee.emit('data', '00101001')

        Assuming ``data`` is an attached function, this will call
        ``data('00101001')'``.
        """
        handled = self._call_handlers(event, args, kwargs)

        if not handled:
            self._emit_handle_potential_error(event, args[0] if args else None)

        return handled

    def once(
        self,
        event: Union[Event, InternalEvent],
        f: Optional[HandlerP[Event, Arg, Kwarg]] = None,
    ) -> Union[HandlerP[Event, Arg, Kwarg], DecoratorP[Event, Arg, Kwarg]]:
        """The same as ``ee.on``, except that the listener is automatically
        removed after being called.
        """

        def _wrapper(f: AnyHandlerP) -> AnyHandlerP:
            def g(
                *args: Union[Arg, Exception, Event, InternalEvent, AnyHandlerP],
                **kwargs: Kwarg,
            ) -> Any:
                with self._lock:
                    # Check that the event wasn't removed already right
                    # before the lock
                    if event in self._events and f in self._events[event]:
                        self._remove_listener(event, f)
                    else:
                        return None
                # f may return a coroutine, so we need to return that
                # result here so that emit can schedule it
                return f(*args, **kwargs)

            self._add_event_handler(event, f, g)
            return f

        if f is None:
            return _wrapper
        else:
            return _wrapper(f)

    def _remove_listener(
        self, event: Union[Event, InternalEvent], f: HandlerP[Event, Arg, Kwarg]
    ) -> None:
        """Naked unprotected removal."""
        self._events[event].pop(f)

    def remove_listener(
        self, event: Union[Event, InternalEvent], f: HandlerP[Event, Arg, Kwarg]
    ) -> None:
        """Removes the function ``f`` from ``event``."""
        with self._lock:
            self._remove_listener(event, f)

    def remove_all_listeners(
        self, event: Optional[Union[Event, InternalEvent]] = None
    ) -> None:
        """Remove all listeners attached to ``event``.
        If ``event`` is ``None``, remove all listeners on all events.
        """
        with self._lock:
            if event is not None:
                self._events[event] = OrderedDict()
            else:
                self._events = defaultdict(OrderedDict)

    def listeners(
        self, event: Union[Event, InternalEvent]
    ) -> List[HandlerP[Event, Arg, Kwarg]]:
        """Returns a list of all listeners registered to the ``event``."""
        return list(self._events[event].keys())


class EventEmitterP(Protocol[IEvent, IArg, IKwarg]):
    """A protocol for event emitters. This may be used to type-check
    EventEmitters structurally.
    """

    def __init__(self) -> None:
        ...

    def on(
        self,
        event: Union[IEvent, InternalEvent],
        f: Optional[HandlerP[IEvent, IArg, IKwarg]] = None,
    ) -> Union[HandlerP[IEvent, IArg, IKwarg], DecoratorP]:
        ...

    def listens_to(
        self, event: Union[IEvent, InternalEvent]
    ) -> DecoratorP[IEvent, IArg, IKwarg]:
        ...

    def add_listener(
        self, event: Union[IEvent, InternalEvent], f: HandlerP[IEvent, IArg, IKwarg]
    ) -> HandlerP[IEvent, IArg, IKwarg]:
        ...

    def emit(
        self,
        event: Union[IEvent, InternalEvent],
        *args: Union[IArg, Exception, IEvent, InternalEvent, AnyHandlerP],
        **kwargs: IKwarg,
    ) -> bool:
        ...

    def once(
        self,
        event: Union[IEvent, InternalEvent],
        f: Optional[HandlerP[IEvent, IArg, IKwarg]] = None,
    ) -> Union[HandlerP[IEvent, IArg, IKwarg], DecoratorP[IEvent, IArg, IKwarg]]:
        ...

    def remove_listener(
        self, event: Union[IEvent, InternalEvent], f: HandlerP[IEvent, IArg, IKwarg]
    ) -> None:
        ...

    def remove_all_listeners(
        self, event: Optional[Union[IEvent, InternalEvent]] = None
    ) -> None:
        ...

    def listeners(
        self, event: Union[IEvent, InternalEvent]
    ) -> List[HandlerP[IEvent, IArg, IKwarg]]:
        ...
