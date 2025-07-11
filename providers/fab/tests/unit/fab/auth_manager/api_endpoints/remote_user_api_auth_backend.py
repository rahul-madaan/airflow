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
"""Default authentication backend - everything is allowed"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, TypeVar, cast

from flask import Response, request
from flask_login import login_user

from airflow.api_fastapi.app import get_auth_manager

if TYPE_CHECKING:
    from requests.auth import AuthBase

    from airflow.providers.fab.auth_manager.fab_auth_manager import FabAuthManager

log = logging.getLogger(__name__)

CLIENT_AUTH: tuple[str, str] | AuthBase | None = None


def init_app(_):
    """Initializes authentication backend"""


T = TypeVar("T", bound=Callable)


def _lookup_user(user_email_or_username: str):
    security_manager = cast("FabAuthManager", get_auth_manager()).security_manager
    user = security_manager.find_user(email=user_email_or_username) or security_manager.find_user(
        username=user_email_or_username
    )
    if not user:
        return None

    if not user.is_active:
        return None

    return user


def requires_authentication(function: T):
    """Decorator for functions that require authentication"""

    @wraps(function)
    def decorated(*args, **kwargs):
        user_id = request.remote_user
        if not user_id:
            log.debug("Missing REMOTE_USER.")
            return Response("Forbidden", 403)

        log.debug("Looking for user: %s", user_id)

        user = _lookup_user(user_id)
        if not user:
            return Response("Forbidden", 403)

        log.debug("Found user: %s", user)

        login_user(user, remember=False)
        return function(*args, **kwargs)

    return cast("T", decorated)
