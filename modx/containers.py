from __future__ import annotations

from dependency_injector import containers
from dependency_injector import providers

import modx.cache
import modx.cache.redis
import modx.chatbot.openai
import modx.client.http
import modx.config
import modx.context
import modx.http
import modx.http.lifespan
import modx.interface
import modx.interface.auth
import modx.interface.compat
import modx.logger
import modx.resources
import modx.resources.api_key
import modx.resources.models
import modx.service
import modx.service.auth
import modx.service.compat


class InfrastructureContainer(containers.DeclarativeContainer):
    config: modx.config.ModXConfig = providers.Singleton(modx.config.get)
    context: modx.context.Context = providers.Singleton(modx.context.Context)
    logger: modx.logger.Logger = providers.Singleton(modx.logger.Logger, config=config)
    api_key: modx.resources.api_key.APIKey = providers.Singleton(
        modx.resources.api_key.APIKey,
        config=config,
        logger=logger,
    )
    models: modx.resources.models.Models = providers.Singleton(
        modx.resources.models.Models,
        config=config,
        logger=logger,
    )
    cache: modx.cache.KVCache[modx.cache.V] = providers.Singleton(
        modx.cache.redis.RedisCache,
        config=config,
        logger=logger,
    )
    http_client: modx.client.http.HTTPClient = providers.Singleton(
        modx.client.http.HTTPClient,
        config=config,
    )
    chatbot: modx.chatbot.Chatbot = providers.Singleton(
        modx.chatbot.openai.ChatCompletion,
        models=models,
        logger=logger,
        http_client=http_client,
        cache=cache,
        config=config,
    )


class ServiceContainer(containers.DeclarativeContainer):
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    auth: modx.service.auth.IAuthService = (providers.Singleton(
        modx.service.auth.AuthService,
        logger=infrastructure.logger,
        api_key=infrastructure.api_key,
    ))
    compat: modx.service.compat.ICompatService = (providers.Singleton(
        modx.service.compat.CompatService,
        logger=infrastructure.logger,
        chatbot=infrastructure.chatbot,
        models=infrastructure.models,
    ))


class InterfaceContainer(containers.DeclarativeContainer):
    infrastructure: InfrastructureContainer = providers.DependenciesContainer()
    services: ServiceContainer = providers.DependenciesContainer()

    auth: modx.interface.auth.IAuthInterface = (providers.Singleton(
        modx.interface.auth.AuthInterface,
        logger=infrastructure.logger,
        auth_service=services.auth,
    ))
    compat: modx.interface.compat.ICompatInterface = (providers.Singleton(
        modx.interface.compat.CompatInterface,
        logger=infrastructure.logger,
        compat_service=services.compat,
    ))


class Container(containers.DeclarativeContainer):
    infrastructure: InfrastructureContainer = (providers.Container(InfrastructureContainer))
    services: ServiceContainer = providers.Container(ServiceContainer,
                                                     infrastructure=infrastructure)
    interfaces: InterfaceContainer = providers.Container(InterfaceContainer,
                                                         infrastructure=infrastructure,
                                                         services=services)
    lifespan: modx.http.lifespan.Lifespan = providers.Singleton(
        modx.http.lifespan.Lifespan,
        logger=infrastructure.logger,
        config=infrastructure.config,
        http_client=infrastructure.http_client,
    )
    http_server: modx.http.HTTPServer = providers.Singleton(
        modx.http.HTTPServer,
        logger=infrastructure.logger,
        config=infrastructure.config,
        context=infrastructure.context,
        lifespan=lifespan,
        auth_interface=interfaces.auth,
    )
