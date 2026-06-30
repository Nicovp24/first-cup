---
title: "IdentityServer4 comercializado"
date: "2026-06-30"
description: "La decisión de Duende de comercializar IdentityServer4 resalta la importancia de la gestión de identidades y acceso en la industria del software y la necesidad de soluciones flexibles y seguras."
tags: ["seguridad", "backend", "open-source"]
cover: "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/rsk-forks-open-identityserver/"
---

La comunidad de desarrolladores se vio afectada cuando la empresa de identidad y control de acceso Duende comercializó su producto de código abierto IdentityServer en diciembre de 2022. El producto, conocido como IdentityServer4, era una solución popular para la gestión de identidades y acceso en aplicaciones web. La decisión de Duende de comercializar el producto generó descontento entre los desarrolladores, quienes habían estado utilizando y contribuyendo al proyecto de código abierto. Puedes leer más sobre este tema en el artículo [IdentityServer4 is dead. Here’s what comes next.](https://thenewstack.io/rsk-forks-open-identityserver/).

## Qué es / Qué ha pasado
IdentityServer4 es un proyecto de código abierto que se encuentra en el repositorio [IdentityServer/IdentityServer4](https://github.com/IdentityServer/IdentityServer4) en GitHub, con más de 7.000 estrellas. El proyecto está escrito en C# y se utiliza para la gestión de identidades y acceso en aplicaciones web. La decisión de Duende de comercializar el producto ha generado un vacío en la comunidad de desarrolladores, quienes buscan alternativas para la gestión de identidades y acceso. El producto de Duende se diferencia de otras soluciones de identidad y acceso en que ofrece una arquitectura modular y flexible, lo que permite a los desarrolladores personalizar y extender su funcionalidad.

## Por qué importa ahora
La comercialización de IdentityServer4 resalta la importancia de la gestión de identidades y acceso en la industria del software. La tendencia hacia la arquitectura de microservicios y la adopción de tecnologías en la nube han aumentado la complejidad de la gestión de identidades y acceso. Las soluciones de identidad y acceso existentes, como OpenID Connect y OAuth 2.0, no siempre son suficientes para satisfacer las necesidades de las aplicaciones modernas. La comunidad de desarrolladores busca soluciones que sean flexibles, escalables y seguras, y que puedan ser personalizadas para satisfacer las necesidades específicas de cada aplicación.

## Detalles técnicos y qué significa para ti
La arquitectura de IdentityServer4 se basa en una arquitectura de microservicios, lo que permite a los desarrolladores personalizar y extender su funcionalidad. El producto utiliza protocolos de autenticación y autorización estándar, como OpenID Connect y OAuth 2.0, y ofrece una API REST para la gestión de identidades y acceso. 
```csharp
using IdentityServer4;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;

public class Startup
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddIdentityServer()
            .AddApiResources(resources =>
            {
                resources.AddApiResource("api1", "My API");
            })
            .AddClients(clients =>
            {
                clients.AddClient("client1", client =>
                {
                    client.ClientId = "client1";
                    client.ClientSecrets.Add(new Secret("secret1".Sha256()));
                    client AllowedGrantTypes = GrantTypes.ClientCredentials;
                });
            });
    }

    public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
    {
        app.UseIdentityServer();
    }
}
```
> "IdentityServer4 es un servidor de autenticación y autorización para ASP.NET Core, que permite a los desarrolladores proteger sus aplicaciones web y APIs con autenticación y autorización basada en estándares abiertos." - [README de IdentityServer4](https://github.com/IdentityServer/IdentityServer4#readme)

La decisión de Duende de comercializar IdentityServer4 puede tener implicaciones prácticas para los desarrolladores que están utilizando el producto. Es posible que deban buscar alternativas para la gestión de identidades y acceso, o pagar por la versión comercializada del producto.

**Bottom line:** La comercialización de IdentityServer4 resalta la importancia de la gestión de identidades y acceso en la industria del software, y la necesidad de soluciones flexibles, escalables y seguras que puedan ser personalizadas para satisfacer las necesidades específicas de cada aplicación.

**Ver también:** [IdentityServer4 is dead. Here’s what comes next.](https://thenewstack.io/rsk-forks-open-identityserver/) · [Documentación de IdentityServer4](https://docs.identityserver.io/en/latest/)
