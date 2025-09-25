from __future__ import annotations

import functools as ft
import time
import typing as t

import prometheus_client as prom
import starlette.types as types

from modx.config.prometheus import PrometheusConfig
from modx.context import Context
from modx.helpers.mixin import LoggingTagMixin
from modx.http.middlewares import BaseMiddleware
from modx.logger import Logger
from modx.utils import ansi as ansi_utils


class PrometheusMiddleware(BaseMiddleware, LoggingTagMixin):
    """Middleware for collecting and exposing Prometheus metrics.

    This middleware automatically collects standard HTTP metrics and provides
    an interface for custom metrics registration. It exposes metrics via a
    configurable endpoint.
    """
    __logging_tag__ = 'modx.http.middlewares.prometheus'

    def __init__(self, app: types.ASGIApp, *, logger: Logger, context: Context,
                 config: PrometheusConfig):
        BaseMiddleware.__init__(self, app)
        LoggingTagMixin.__init__(self, logger)

        self.context = context
        self.config = config
        self.metrics_path = self.config.metrics_path
        self.track_in_progress = self.config.track_in_progress
        self.exclude_paths = (self.config.exclude_paths or {self.config.metrics_path})
        self.custom_labels = self.config.custom_labels or {}
        self.enable_exemplars = self.config.enable_exemplars
        self.app_name = self.config.app_name
        self.app_version = self.config.app_version

        # Default histogram buckets for response time
        self.buckets = self.config.buckets or (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5,
                                               0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf'))

        # Initialize standard metrics
        self._init_standard_metrics()

        # Custom metrics registry
        self._custom_metrics: t.Dict[str, t.Any] = {}
        self._metric_collectors: t.Dict[str, t.Callable] = {}

    def _get_base_labels(self) -> t.List[str]:
        """Get base label names for all metrics."""
        base_labels = ["method", "endpoint", "status_code"]
        base_labels.extend(self.custom_labels.keys())
        return base_labels

    def _get_label_values(self, method: str, path: str, status_code: int,
                          **extra_labels: str) -> t.Dict[str, str]:
        """Get label values for metrics."""
        labels = {
            "method": method,
            "endpoint": self._normalize_path(path),
            "status_code": str(status_code),
            **self.custom_labels,
            **extra_labels
        }
        return labels

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path for metrics (e.g., replace IDs with placeholders)."""
        # Simple normalization - can be extended based on routing patterns
        import re

        # Replace UUIDs
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                      '/{uuid}',
                      path,
                      flags=re.IGNORECASE)

        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)

        # Replace common patterns
        path = re.sub(r'/v\d+/', '/v{version}/', path)

        return path

    def _init_standard_metrics(self) -> None:
        """Initialize standard Prometheus metrics."""
        base_labels = self._get_base_labels()

        # Request counter
        self.request_count = prom.Counter('http_requests_total', 'Total number of HTTP requests',
                                          base_labels)

        # Response time histogram
        self.request_duration = prom.Histogram('http_request_duration_seconds',
                                               'HTTP request duration in seconds',
                                               base_labels,
                                               buckets=self.buckets)

        # Request size histogram
        self.request_size = prom.Histogram('http_request_size_bytes',
                                           'HTTP request size in bytes',
                                           base_labels,
                                           buckets=(100, 1000, 10000, 100000, 1000000, 10000000,
                                                    float('inf')))

        # Response size histogram
        self.response_size = prom.Histogram('http_response_size_bytes',
                                            'HTTP response size in bytes',
                                            base_labels,
                                            buckets=(100, 1000, 10000, 100000, 1000000, 10000000,
                                                     float('inf')))

        # Requests in progress gauge
        if self.track_in_progress:
            self.requests_in_progress = prom.Gauge(
                'http_requests_in_progress', 'Number of HTTP requests currently being processed',
                ["method", "endpoint"] + list(self.custom_labels.keys()))

        # Application info
        self.app_info = prom.Info('asgi_app_info', 'ASGI application information')
        self.app_info.info({'name': self.app_name, 'version': self.app_version})

        # Error counter
        self.error_count = prom.Counter('http_errors_total', 'Total number of HTTP errors',
                                        base_labels + ["error_type"])

    def register_counter(self,
                         name: str,
                         description: str,
                         labels: t.Optional[t.List[str]] = None) -> prom.Counter:
        """Register a custom counter metric."""
        labels = labels or []
        counter = prom.Counter(name, description, labels)
        self._custom_metrics[name] = counter
        return counter

    def register_histogram(self,
                           name: str,
                           description: str,
                           labels: t.Optional[t.List[str]] = None,
                           buckets: t.Optional[t.Tuple[float, ...]] = None) -> prom.Histogram:
        """Register a custom histogram metric."""
        labels = labels or []
        histogram = prom.Histogram(name, description, labels, buckets=buckets)
        self._custom_metrics[name] = histogram
        return histogram

    def register_gauge(self,
                       name: str,
                       description: str,
                       labels: t.Optional[t.List[str]] = None) -> prom.Gauge:
        """Register a custom gauge metric."""
        labels = labels or []
        gauge = prom.Gauge(name, description, labels)
        self._custom_metrics[name] = gauge
        return gauge

    def register_enum(self,
                      name: str,
                      description: str,
                      labels: t.Optional[t.List[str]] = None,
                      states: t.Optional[t.List[str]] = None) -> prom.Enum:
        """Register a custom enum metric."""
        labels = labels or []
        states = states or []
        enum_metric = prom.Enum(name, description, labels, states=states)
        self._custom_metrics[name] = enum_metric
        return enum_metric

    def register_info(self,
                      name: str,
                      description: str,
                      labels: t.Optional[t.List[str]] = None) -> prom.Info:
        """Register a custom info metric."""
        labels = labels or []
        info_metric = prom.Info(name, description, labels)
        self._custom_metrics[name] = info_metric
        return info_metric

    def add_metric_collector(self, name: str,
                             collector_func: t.Callable[[], t.Dict[str, t.Any]]) -> None:
        """Add a custom metric collector function."""
        self._metric_collectors[name] = collector_func

    def get_metric(self, name: str) -> t.Optional[t.Any]:
        """Get a registered custom metric by name."""
        return self._custom_metrics.get(name)

    def _collect_custom_metrics(self) -> None:
        """Collect metrics from registered collectors."""
        for name, collector in self._metric_collectors.items():
            try:
                metrics_data = collector()
                self._update_metrics_from_data(metrics_data)
            except Exception as e:
                self.logger.error(f"Error collecting custom metrics from {name}: {e}")

    def _update_metrics_from_data(self, data: t.Dict[str, t.Any]) -> None:
        """Update metrics from collected data."""
        # This can be extended based on specific needs
        pass

    @staticmethod
    def _get_request_size(scope: t.MutableMapping[str, t.Any]) -> int:
        """Calculate request size from scope."""
        size = 0

        # Add headers size
        for name, value in scope.get('headers', []):
            size += len(name) + len(value) + 4  # ": " and "\r\n"

        # Add content length if available
        content_length = None
        for name, value in scope.get('headers', []):
            if name.lower() == b'content-length':
                try:
                    content_length = int(value.decode())
                    break
                except (ValueError, UnicodeDecodeError):
                    pass

        if content_length:
            size += content_length

        return size

    def _extract_exemplar(self) -> t.Optional[t.Dict[str, str]]:
        """Extract exemplar data from context if tracing is enabled."""
        if not self.enable_exemplars:
            return None

        trace_id = self.context.get('trace_id')
        span_id = self.context.get('span_id')

        if trace_id and span_id:
            return {"trace_id": trace_id, "span_id": span_id}
        return None

    async def _handle_metrics_request(self, send: types.Send) -> None:
        """Handle metrics endpoint request."""
        try:
            # Collect custom metrics
            self._collect_custom_metrics()

            # Generate metrics output
            metrics_output = prom.generate_latest(prom.REGISTRY)

            # Send response
            await send({
                "type":
                    "http.response.start",
                "status":
                    200,
                "headers": [
                    (b"content-type", prom.CONTENT_TYPE_LATEST.encode()),
                    (b"content-length", str(len(metrics_output)).encode()),
                ]
            })
            await send({"type": "http.response.body", "body": metrics_output})

            self.logger.debug(
                ansi_utils.ANSIFormatter.format("Served Prometheus metrics",
                                                ansi_utils.ANSIFormatter.FG.GREEN))

        except Exception as e:
            error_msg = f"Error serving metrics: {str(e)}"
            error_body = error_msg.encode()

            await send({
                "type":
                    "http.response.start",
                "status":
                    500,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(error_body)).encode()),
                ]
            })
            await send({"type": "http.response.body", "body": error_body})

            self.logger.error(
                ansi_utils.ANSIFormatter.format(f"❌ {error_msg}", ansi_utils.ANSIFormatter.FG.RED))

    async def __call__(self, scope: types.Scope, receive: types.Receive, send: types.Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        # Handle metrics endpoint
        if path == self.metrics_path:
            await self._handle_metrics_request(send)
            return

        # Skip excluded paths
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request_size = self._get_request_size(scope)

        # Track in-progress requests
        if self.track_in_progress:
            progress_labels = {
                "method": method,
                "endpoint": self._normalize_path(path),
                **self.custom_labels
            }
            self.requests_in_progress.labels(**progress_labels).inc()

        # Response tracking variables
        status_code = 500  # Default to error
        response_size = 0
        error_type = None

        async def send_wrapper(message: t.MutableMapping[str, t.Any]) -> None:
            nonlocal status_code, response_size

            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_size += len(body)

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(f"Request failed with {error_type}: {str(e)}")
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Get label values
            labels = self._get_label_values(method, path, status_code)
            exemplar = self._extract_exemplar()

            # Record metrics
            self.request_count.labels(**labels).inc()

            if exemplar:
                self.request_duration.labels(**labels).observe(duration, exemplar=exemplar)
            else:
                self.request_duration.labels(**labels).observe(duration)

            self.request_size.labels(**labels).observe(request_size)
            self.response_size.labels(**labels).observe(response_size)

            # Record errors
            if status_code >= 400 or error_type:
                error_labels = {**labels, "error_type": error_type or "http_error"}
                self.error_count.labels(**error_labels).inc()

            # Update in-progress counter
            if self.track_in_progress:
                progress_labels = {
                    "method": method,
                    "endpoint": self._normalize_path(path),
                    **self.custom_labels
                }
                self.requests_in_progress.labels(**progress_labels).dec()

            # Log metrics collection
            self.logger.debug(
                ansi_utils.ANSIFormatter.format(
                    f"📊 Metrics recorded: {method} {path} -> {status_code} "
                    f"({duration:.3f}s, {response_size}B)", ansi_utils.ANSIFormatter.FG.BLUE))


# Utility decorator for custom metric collection
def collect_metric(middleware: PrometheusMiddleware, metric_name: str):
    """Decorator to automatically collect metrics from function execution."""

    def decorator(func):

        @ft.wraps(func)
        async def async_wrapper(*args, **kwargs):
            metric = middleware.get_metric(metric_name)
            if metric and hasattr(metric, 'time'):
                with metric.time():
                    return await func(*args, **kwargs)
            return await func(*args, **kwargs)

        @ft.wraps(func)
        def sync_wrapper(*args, **kwargs):
            metric = middleware.get_metric(metric_name)
            if metric and hasattr(metric, 'time'):
                with metric.time():
                    return func(*args, **kwargs)
            return func(*args, **kwargs)

        if (hasattr(func, '__code__') and func.__code__.co_flags & 0x80):  # CO_COROUTINE
            return async_wrapper
        return sync_wrapper

    return decorator
