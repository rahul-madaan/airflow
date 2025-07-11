#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from airflow.configuration import conf
from airflow.exceptions import AirflowException
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.http.triggers.http import HttpSensorTrigger
from airflow.providers.http.version_compat import AIRFLOW_V_3_0_PLUS

if AIRFLOW_V_3_0_PLUS:
    from airflow.sdk import BaseSensorOperator
else:
    from airflow.sensors.base import BaseSensorOperator  # type: ignore[no-redef]

if TYPE_CHECKING:
    try:
        from airflow.sdk.definitions.context import Context

        if AIRFLOW_V_3_0_PLUS:
            from airflow.sdk import PokeReturnValue
        else:
            from airflow.sensors.base import PokeReturnValue  # type: ignore[no-redef]
    except ImportError:
        # TODO: Remove once provider drops support for Airflow 2
        from airflow.utils.context import Context


class HttpSensor(BaseSensorOperator):
    """
    Execute HTTP GET statement; return False on failure 404 Not Found or `response_check` returning False.

    HTTP Error codes other than 404 (like 403) or Connection Refused Error
    would raise an exception and fail the sensor itself directly (no more poking).
    To avoid failing the task for other codes than 404, the argument ``response_error_codes_allowlist``
    can be passed with the list containing all the allowed error status codes, like ``["404", "503"]``
    To skip error status code check at all, the argument ``extra_option``
    can be passed with the value ``{'check_response': False}``. It will make the ``response_check``
    be execute for any http status code.

    The response check can access the template context to the operator:

    .. code-block:: python

        def response_check(response, task_instance):
            # The task_instance is injected, so you can pull data form xcom
            # Other context variables such as dag, ds, logical_date are also available.
            xcom_data = task_instance.xcom_pull(task_ids="pushing_task")
            # In practice you would do something more sensible with this data..
            print(xcom_data)
            return True


        HttpSensor(task_id="my_http_sensor", ..., response_check=response_check)

    .. seealso::
        For more information on how to use this operator, take a look at the guide:
        :ref:`howto/operator:HttpSensor`

    :param http_conn_id: The :ref:`http connection<howto/connection:http>` to run the
        sensor against
    :param method: The HTTP request method to use
    :param endpoint: The relative part of the full url
    :param request_params: The parameters to be added to the GET url
    :param headers: The HTTP headers to be added to the GET request
    :param response_error_codes_allowlist: An allowlist to return False on poke(), not to raise exception.
        If the ``None`` value comes in, it is assigned ["404"] by default, for backward compatibility.
        When you also want ``404 Not Found`` to raise the error, explicitly deliver the blank list ``[]``.
    :param response_check: A check against the 'requests' response object.
        The callable takes the response object as the first positional argument
        and optionally any number of keyword arguments available in the context dictionary.
        It should return True for 'pass' and False otherwise.
    :param extra_options: Extra options for the 'requests' library, see the
        'requests' documentation (options to modify timeout, ssl, etc.)
    :param tcp_keep_alive: Enable TCP Keep Alive for the connection.
    :param tcp_keep_alive_idle: The TCP Keep Alive Idle parameter (corresponds to ``socket.TCP_KEEPIDLE``).
    :param tcp_keep_alive_count: The TCP Keep Alive count parameter (corresponds to ``socket.TCP_KEEPCNT``)
    :param tcp_keep_alive_interval: The TCP Keep Alive interval parameter (corresponds to
        ``socket.TCP_KEEPINTVL``)
    :param deferrable: If waiting for completion, whether to defer the task until done,
        default is ``False``
    """

    template_fields: Sequence[str] = ("endpoint", "request_params", "headers")

    def __init__(
        self,
        *,
        endpoint: str,
        http_conn_id: str = "http_default",
        method: str = "GET",
        request_params: dict[str, Any] | None = None,
        request_kwargs: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        response_error_codes_allowlist: list[str] | None = None,
        response_check: Callable[..., bool | PokeReturnValue] | None = None,
        extra_options: dict[str, Any] | None = None,
        tcp_keep_alive: bool = True,
        tcp_keep_alive_idle: int = 120,
        tcp_keep_alive_count: int = 20,
        tcp_keep_alive_interval: int = 30,
        deferrable: bool = conf.getboolean("operators", "default_deferrable", fallback=False),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.http_conn_id = http_conn_id
        self.method = method
        self.response_error_codes_allowlist = (
            ("404",) if response_error_codes_allowlist is None else tuple(response_error_codes_allowlist)
        )
        self.request_params = request_params or {}
        self.headers = headers or {}
        self.extra_options = extra_options or {}
        self.response_check = response_check
        self.tcp_keep_alive = tcp_keep_alive
        self.tcp_keep_alive_idle = tcp_keep_alive_idle
        self.tcp_keep_alive_count = tcp_keep_alive_count
        self.tcp_keep_alive_interval = tcp_keep_alive_interval
        self.deferrable = deferrable
        self.request_kwargs = request_kwargs or {}

    def poke(self, context: Context) -> bool | PokeReturnValue:
        from airflow.utils.operator_helpers import determine_kwargs

        hook = HttpHook(
            method=self.method,
            http_conn_id=self.http_conn_id,
            tcp_keep_alive=self.tcp_keep_alive,
            tcp_keep_alive_idle=self.tcp_keep_alive_idle,
            tcp_keep_alive_count=self.tcp_keep_alive_count,
            tcp_keep_alive_interval=self.tcp_keep_alive_interval,
        )

        self.log.info("Poking: %s", self.endpoint)
        try:
            response = hook.run(
                self.endpoint,
                data=self.request_params,
                headers=self.headers,
                extra_options=self.extra_options,
                **self.request_kwargs,
            )

            if self.response_check:
                kwargs = determine_kwargs(self.response_check, [response], context)

                return self.response_check(response, **kwargs)

        except AirflowException as exc:
            if str(exc).startswith(self.response_error_codes_allowlist):
                return False
            raise exc

        return True

    def execute(self, context: Context) -> Any:
        if not self.deferrable or self.response_check:
            return super().execute(context=context)
        if not self.poke(context):
            self.defer(
                timeout=timedelta(seconds=self.timeout),
                trigger=HttpSensorTrigger(
                    endpoint=self.endpoint,
                    http_conn_id=self.http_conn_id,
                    data=self.request_params,
                    headers=self.headers,
                    method=self.method,
                    extra_options=self.extra_options,
                    poke_interval=self.poke_interval,
                ),
                method_name="execute_complete",
            )

    def execute_complete(self, context: Context, event: dict[str, Any] | None = None) -> None:
        self.log.info("%s completed successfully.", self.task_id)
