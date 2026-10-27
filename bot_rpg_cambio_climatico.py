import asyncio
import json
import os
import random
from pathlib import Path

import discord
from discord.ext import commands

TOKEN = ("MTM2NjEzMTc2Mzg2ODYwMjU0MA.GWvZMG.sOc5IEW4InmBaSnwA9ahlQTsnGFwlkBhfDVunw")

# El archivo se crea automáticamente y guarda personajes aunque cierres el bot.
DATA_FILE = Path(__file__).with_name("jugadores.json")

intents = discord.Intents.default()
intents.message_content = True  # También debes activarlo en el Developer Portal.

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def cargar_jugadores():
    """Carga los personajes y agrega valores faltantes a los perfiles antiguos."""
    if not DATA_FILE.exists():
        return {}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, dict):
            return {}

        # Valores predeterminados para perfiles creados con versiones anteriores.
        # setdefault conserva los valores existentes y solo agrega claves ausentes.
        valores_predeterminados = {
            "nivel": 1,
            "xp": 0,
            "oro": 20,
            "vida": 50,
            "vida_max": 50,
            "ataque": 10,
            "pociones": 3,
            "pociones de ATK": 1,
            "pts_magia": 10,
            "pocion_atk_turnos": 0,
            "combate": None,
        }

        for jugador in datos.values():
            if not isinstance(jugador, dict):
                continue
            for clave, valor in valores_predeterminados.items():
                jugador.setdefault(clave, valor)
            jugador.setdefault("nombre", "Ecoexplorador")

        return datos

    except (json.JSONDecodeError, OSError):
        print("No se pudo leer jugadores.json. Revisa el archivo antes de continuar.")
        return {}


def guardar_jugadores():
    """Guarda los personajes en un archivo JSON."""
    temporal = DATA_FILE.with_suffix(".tmp")
    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(jugadores, archivo, ensure_ascii=False, indent=2)
    temporal.replace(DATA_FILE)


jugadores = cargar_jugadores()


# Monstruos disponibles. Sus estadísticas aumentan un poco según el nivel del jugador.
MONSTRUOS = [
    {"nombre": "Ola de calor", "vida": 24, "ataque": (3, 7), "xp": 18, "oro": (5, 10)},
    {"nombre": "Sequía extrema", "vida": 30, "ataque": (4, 8), "xp": 24, "oro": (7, 13)},
    {"nombre": "Incendio forestal", "vida": 36, "ataque": (5, 9), "xp": 30, "oro": (9, 16)},
    {"nombre": "Inundación repentina", "vida": 42, "ataque": (6, 10), "xp": 36, "oro": (11, 19)},
    {"nombre": "Contaminación por plásticos", "vida": 48, "ataque": (7, 11), "xp": 42, "oro": (13, 22)},
]


def obtener_jugador(ctx):
    """Devuelve el personaje de quien ejecuta el comando, o None si no existe."""
    return jugadores.get(str(ctx.author.id))


def subir_nivel_si_corresponde(jugador):
    """Sube de nivel si el personaje reunió suficiente experiencia."""
    mensajes = []
    while jugador["xp"] >= jugador["nivel"] * 50:
        jugador["xp"] -= jugador["nivel"] * 50
        jugador["nivel"] += 1
        jugador["vida_max"] += 12
        jugador["ataque"] += 2
        jugador["vida"] = jugador["vida_max"]
        mensajes.append(
            f"🎉 ¡Subiste al nivel {jugador['nivel']}! "
            f"Ahora tienes {jugador['vida_max']} puntos de energía máximos y {jugador['ataque']} de mitigación."
        )
    return mensajes


async def turno_monstruo(ctx, jugador):
    """Hace que el monstruo ataque una vez. Devuelve el texto del resultado."""
    monstruo = jugador["combate"]
    danio = random.randint(*monstruo["ataque"])
    jugador["vida"] = max(0, jugador["vida"] - danio)
    texto = f"🌡️ **{monstruo['nombre']}** te afecta y reduce tu energía en **{danio}** puntos."

    if jugador["vida"] <= 0:
        jugador["combate"] = None
        texto += "\n🌪️ La amenaza te ha superado por ahora. Vuelves con 20 de energía y pierdes 10 eco-puntos y 25 XP."
        jugador["vida"] = 20
        jugador["oro"] = max(0, jugador["oro"] - 10)
        jugador["xp"] = max(0, jugador["xp"] - 25)
    else:
        texto += f"\n💚 Tu energía: **{jugador['vida']}/{jugador['vida_max']}**"
    return texto


@bot.event
async def on_ready():
    print(f"¡Bot conectado como {bot.user}!")
    print("Escribe !ayuda en tu servidor para ver los comandos.")


@bot.command(name="crear")
async def crear(ctx, *, nombre: str = None):
    """Crea un personaje. Ejemplo: !crear Luna"""
    user_id = str(ctx.author.id)
    if user_id in jugadores:
        await ctx.send("Ya tienes un ecoexplorador. Usa `!perfil` para ver sus estadísticas.")
        return

    nombre = (nombre or ctx.author.display_name).strip()[:24]
    if not nombre:
        nombre = ctx.author.display_name[:24] or "Ecoexplorador"

    jugadores[user_id] = {
        "nombre": nombre,
        "nivel": 1, # nivel inicial del jugador
        "xp": 0, # experiencia inicial del jugador
        "oro": 20, # oro inicial del jugador
        "vida": 50, # vida inicial del jugador
        "vida_max": 50, # vida máxima inicial del jugador
        "ataque": 10, # ataque inicial del jugador
        "pociones": 3, # pociones iniciales del jugador
        "pociones de ATK": 1, # solo puedes usar 1 a la vez, y dura 3 turnos
        "pts_magia": 10, # puntos de magia iniciales del jugador
        "pocion_atk_turnos": 0, # contador de turnos de la pocion de ataque, si es 0 no hay efecto
        "combate": None, # estado de combate del jugador, None si no está en combate
    }
    guardar_jugadores()
    await ctx.send(
        f"🌱 ¡Bienvenido/a, **{nombre}**! Tu misión para proteger el planeta comienza ahora.\n"
        f"💚 Energía: **50** | 🌿 Mitigación: **10** | 🧰 Kits de recuperación: **3** | 🌱 Refuerzos ecológicos: **1** | ♻️ Eco-puntos: **20**\n"
        f"⚡ Energía verde: **10**\n"
        "Usa `!explorar` para comenzar tu primera misión."
    )


@bot.command(name="perfil")
async def perfil(ctx):
    """Muestra las estadísticas del personaje."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    estado = "🌡️ En misión" if jugador["combate"] else "🌿 Fuera de misión"
    await ctx.send(
        f"🌍 **Perfil ecológico de {jugador['nombre']}**\n"
        f"⭐ Nivel: **{jugador['nivel']}** | ✨ XP: **{jugador['xp']}/{jugador['nivel'] * 50}**\n"
        f"💚 Energía: **{jugador['vida']}/{jugador['vida_max']}**\n"
        f"🌿 Mitigación: **{jugador['ataque']}**\n"
        f"🧰 Kits de recuperación: **{jugador['pociones']}** | 🌱 Refuerzos ecológicos: **{jugador['pociones de ATK']}** | ♻️ Eco-puntos: **{jugador['oro']}**\n"
        f"⚡ Energía verde: **{jugador['pts_magia']}**\n"
        f"Estado: **{estado}**"
    )


@bot.command(name="combate_directo")
async def combate_directo(ctx):
    """Encuentra un monstruo y comienza un combate por turnos."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    if jugador["vida"] <= 0:
        await ctx.send("Tu energía está muy baja. Busca suministros y cuídate antes de seguir.")
        return
    if jugador["combate"]:
        await ctx.send("Ya estás en una misión. Usa `!atacar`, `!magia`, `!pocion`, `!pocion_ATK` o `!huir`.")
        return

    plantilla = random.choice(MONSTRUOS)
    nivel_extra = jugador["nivel"] - 1
    jugador["combate"] = {
        "nombre": plantilla["nombre"],
        "vida": plantilla["vida"] + nivel_extra * 5,
        "vida_max": plantilla["vida"] + nivel_extra * 5,
        "ataque": (plantilla["ataque"][0] + nivel_extra, plantilla["ataque"][1] + nivel_extra),
        "xp": plantilla["xp"] + nivel_extra * 5,
        "oro": plantilla["oro"],
    }
    guardar_jugadores()
    monstruo = jugador["combate"] 
    await ctx.send(
        f"🌍 **¡Aparece una amenaza climática: {monstruo['nombre']}!**\n"
        f"🌡️ Intensidad de la amenaza: **{monstruo['vida']}/{monstruo['vida_max']}**\n"
        f"💚 Tu energía: **{jugador['vida']}/{jugador['vida_max']}**\n"
        f"⚡ Energía verde: **{jugador['pts_magia']}**\n"
        
        "+1 punto de energía verde al mitigar *(MÁX. 10)*\n"
        
        "Tu turno: usa `!atacar`, `!magia`, `!pocion`, `!pocion_ATK`, o `!huir`."
    )


@bot.command(name="explorar")
async def explorar(ctx):
    """Explora el área buscando objetos y cofres; puede que encuentres oro, pociones o un monstruo."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    if jugador["combate"]:
        await ctx.send("Ya estás en una misión. Usa `!atacar`, `!magia`, `!pocion`, `!pocion_ATK` o `!huir`.")
        return

    evento = random.choices(
        ["oro", "pocion", "monstruo", "nada"],
        weights=[0.4, 0.2, 0.3, 0.1],
        k=1
    )[0]
    # dura unos segundos en explorar, para simular que el jugador está buscando
    await ctx.send("🌎 Estás explorando el entorno en busca de soluciones y suministros...")
    await asyncio.sleep(10, 16)  # Simula el tiempo de exploración
    if evento == "oro":
        cantidad = random.randint(25, 50)
        jugador["oro"] += cantidad
        guardar_jugadores()
        await ctx.send(f"♻️ Encontraste recursos aprovechables por **{cantidad} eco-puntos**.")
    elif evento == "pocion":
        jugador["pociones"] += 1
        guardar_jugadores()
        await ctx.send("🧰 Encontraste un kit de recuperación y lo guardaste en tu inventario.")
    elif evento == "monstruo":
        await combate_directo(ctx)  # Llama a la función de combate_directo para iniciar un combate.
    else:
        await ctx.send("🌿 No encontraste suministros esta vez. ¡Sigue explorando y cuidando el planeta!")


@bot.command(name="atacar")
async def atacar(ctx):
    """Ataca al monstruo y, si sigue vivo, recibe su contraataque."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    monstruo = jugador["combate"]
    if not monstruo:
        await ctx.send("No estás en una misión. Usa `!combate_directo` para afrontar una amenaza climática.")
        return

    danio = random.randint(max(1, jugador["ataque"] - 2), jugador["ataque"] + 3)
    monstruo["vida"] = max(0, monstruo["vida"] - danio)
    texto = f"🌿 Aplicas una acción de mitigación contra **{monstruo['nombre']}** y reduces su intensidad en **{danio}**."
    jugador["pts_magia"] = min(10, jugador["pts_magia"] + 1)

    if monstruo["vida"] <= 0:
        xp_ganada = monstruo["xp"]
        oro_ganado = random.randint(*monstruo["oro"])
        jugador["xp"] += xp_ganada
        jugador["oro"] += oro_ganado
        nombre_monstruo = monstruo["nombre"]
        jugador["combate"] = None
        texto += (
            f"\n🌱 ¡Superaste la amenaza {nombre_monstruo}! Ganaste **{xp_ganada} XP** "
            f"y **{oro_ganado} eco-puntos**."
        )
    #una vez que el jugador ataca, si tiene pocion de ATK activa, se reduce el contador de turnos
        if jugador.get("pocion_atk_turnos", 0) > 0:
            jugador["pocion_atk_turnos"] -= 1
            if jugador["pocion_atk_turnos"] == 0:
                jugador["ataque"] -= 5
                texto += "\n🌱 El efecto del refuerzo ecológico ha terminado."
                
        texto += "\n" + "\n".join(subir_nivel_si_corresponde(jugador)) if jugador["xp"] >= jugador["nivel"] * 50 else ""
        texto += "\nUsa `!combate_directo` para afrontar otra amenaza climática."
        
    else:
        texto += f"\n🌡️ Intensidad de {monstruo['nombre']}: **{monstruo['vida']}/{monstruo['vida_max']}**"
        texto += "\n" + await turno_monstruo(ctx, jugador)
        # una vez se pasen 3 turnos con la pocion de ATK activa, esta se acabara y el ataque volvera a la normalidad
        if jugador.get("pocion_atk_turnos", 0) > 0:
            jugador["pocion_atk_turnos"] -= 1
            if jugador["pocion_atk_turnos"] == 0:
                jugador["ataque"] -= 5
                texto += "\n🌱 El efecto del refuerzo ecológico ha terminado."
    guardar_jugadores()
        
    await ctx.send(texto)


@bot.command(name="magia")
async def magia(ctx):
    """Usa magia para atacar al monstruo; consume 5 puntos de magia y tu turno."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    monstruo = jugador["combate"]
    if not monstruo:
        await ctx.send("No estás en una misión. Usa `!combate_directo` para afrontar una amenaza climática.")
        return
    if jugador["pts_magia"] < 5:
        await ctx.send("❌ No tienes suficiente energía verde para esta acción.")
        return

    jugador["pts_magia"] -= 5
    danio = random.randint(max(1, jugador["ataque"] - 1), jugador["ataque"] + 5) + 7  # Magia hace más daño
    monstruo["vida"] = max(0, monstruo["vida"] - danio)
    texto = f"⚡ Usas energía verde contra **{monstruo['nombre']}** y reduces su intensidad en **{danio}**."

    if monstruo["vida"] <= 0:
        xp_ganada = monstruo["xp"]
        oro_ganado = random.randint(*monstruo["oro"])
        jugador["xp"] += xp_ganada
        jugador["oro"] += oro_ganado
        nombre_monstruo = monstruo["nombre"]
        jugador["combate"] = None
        texto += (
            f"\n🌱 ¡Superaste la amenaza {nombre_monstruo}! Ganaste **{xp_ganada} XP** "
            f"y **{oro_ganado} eco-puntos**."
        )
        #una vez que el jugador ataca, si tiene pocion de ATK activa, se reduce el contador de turnos
        if jugador.get("pocion_atk_turnos", 0) > 0:
            jugador["pocion_atk_turnos"] -= 1
            if jugador["pocion_atk_turnos"] == 0:
                jugador["ataque"] -= 5
                texto += "\n🌱 El efecto del refuerzo ecológico ha terminado."
                    
        texto += "\n" + "\n".join(subir_nivel_si_corresponde(jugador)) if jugador["xp"] >= jugador["nivel"] * 50 else ""
        texto += "\nUsa `!combate_directo` para afrontar otra amenaza climática."
    else:
        texto += f"\n🌡️ Intensidad de {monstruo['nombre']}: **{monstruo['vida']}/{monstruo['vida_max']}**"
        texto += "\n" + await turno_monstruo(ctx, jugador)
        #una vez que el jugador ataca, si tiene pocion de ATK activa, se reduce el contador de turnos
        if jugador.get("pocion_atk_turnos", 0) > 0:
            jugador["pocion_atk_turnos"] -= 1
            if jugador["pocion_atk_turnos"] == 0:
                jugador["ataque"] -= 5
                texto += "\n🌱 El efecto del refuerzo ecológico ha terminado."

    guardar_jugadores()
    await ctx.send(texto)


@bot.command(name="pocion")
async def pocion(ctx):
    """Usa una poción para recuperar 30 HP; hacerlo consume tu turno."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    if not jugador["combate"]:
        await ctx.send("Solo puedes usar `!pocion` durante una misión.")
        return
    if jugador["pociones"] <= 0:
        await ctx.send("No te quedan kits de recuperación. ¡Administra tus recursos!")
        return
    if jugador["vida"] >= jugador["vida_max"]:
        await ctx.send("Tu energía está al máximo. Guarda el kit para después.")
        return

    anterior = jugador["vida"]
    jugador["vida"] = min(jugador["vida_max"], jugador["vida"] + 30)
    curacion = jugador["vida"] - anterior
    jugador["pociones"] -= 1
    texto = f"🧰 Usas un kit de recuperación y restauras **{curacion} puntos de energía**. Energía: **{jugador['vida']}/{jugador['vida_max']}**."
    texto += "\n" + await turno_monstruo(ctx, jugador)
    guardar_jugadores()
    await ctx.send(texto)


@bot.command(name="pocion_ATK")
async def pocion_atk(ctx):
    """Usa una poción de ataque para aumentar tu ataque durante 3 turnos; hacerlo consume tu turno."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    if not jugador["combate"]:
        await ctx.send("Solo puedes usar `!pocion_ATK` durante una misión.")
        return
    if jugador["pociones de ATK"] <= 0:
        await ctx.send("No te quedan refuerzos ecológicos. ¡Administra tus recursos!")
        return

    jugador["ataque"] += 5
    jugador["pociones de ATK"] -= 1
    jugador["pocion_atk_turnos"] = 3
    texto = "🌱 Activas un refuerzo ecológico y tu mitigación aumenta en **5** durante 3 turnos."
    texto += "\n" + await turno_monstruo(ctx, jugador)
    guardar_jugadores()
    await ctx.send(texto)


@bot.command(name="huir")
async def huir(ctx):
    """Intenta escapar del combate; el monstruo puede golpearte al huir."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return
    if not jugador["combate"]:
        await ctx.send("No estás afrontando ninguna amenaza ahora mismo.")
        return

    if random.random() < 0.65:
        nombre_monstruo = jugador["combate"]["nombre"]
        jugador["combate"] = None
        guardar_jugadores()
        await ctx.send(f"🍃 Te retiraste de la amenaza {nombre_monstruo}. Puedes volver a intentarlo con `!combate_directo`.")
    else:
        texto = "🌪️ ¡No lograste retirarte a tiempo!\n" + await turno_monstruo(ctx, jugador)
        guardar_jugadores()
        await ctx.send(texto)


@bot.command(name="eliminar_perfil")
async def eliminarperfil(ctx, confirmacion: str = None):
    """Elimina el personaje del usuario; requiere confirmación explícita."""
    user_id = str(ctx.author.id)
    jugador = jugadores.get(user_id)

    if not jugador:
        await ctx.send("No tienes un ecoexplorador que eliminar. Usa `!crear Nombre` para crear uno.")
        return

    if (confirmacion or "").lower() != "confirmar":
        await ctx.send(
            f"⚠️ **¿Seguro que quieres eliminar el perfil de {jugador['nombre']}?**\n"
            "Esto borrará permanentemente tu nivel, experiencia, eco-puntos, kits y progreso.\n"
            "Para confirmar, escribe `!eliminar_perfil_confirmar`. Si cambiaste de opinión, no hagas nada."
        )
        return


@bot.command(name="eliminar_perfil_confirmar")
async def eliminarperfil_confirmar(ctx):
    """Confirma la eliminación del personaje del usuario."""
    user_id = str(ctx.author.id)
    jugador = jugadores.get(user_id)
    if not jugador:
        await ctx.send("No tienes un ecoexplorador que eliminar. Usa `!crear Nombre` para crear uno.")
        return

    nombre = jugador["nombre"]
    del jugadores[user_id]
    guardar_jugadores()
    await ctx.send(
        f"🗑️ Se ha eliminado el perfil ecológico de **{nombre}** y todo su progreso.\n"
        "Puedes empezar de nuevo cuando quieras con `!crear Nombre`."
    )


@bot.command(name="tienda")
async def tienda(ctx):
    """Muestra los comandos disponibles en la tienda."""
    await ctx.send(
        "♻️ **Centro de suministros ecológicos**\n"
        "`!comprar_pocion` — compra un kit de recuperación por 50 eco-puntos (restaura hasta 30 de energía).\n"
        "`!vender_pocion` — vende un kit de recuperación por 30 eco-puntos.\n"
        "`!comprar_pocion_ATK` — compra un refuerzo ecológico por 80 eco-puntos (aumenta la mitigación durante 3 turnos).\n"
        "`!vender_pocion_ATK` — vende un refuerzo ecológico por 60 eco-puntos.\n"
    )


@bot.command(name="comprar_pocion")
async def comprarpocion(ctx):
    """Compra una pocion por 50 de oro."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    if jugador["oro"] < 50:
        await ctx.send("❌ No tienes suficientes eco-puntos para comprar un kit de recuperación.")
        return

    jugador["oro"] -= 50
    jugador["pociones"] += 1
    guardar_jugadores()
    await ctx.send("🧰 Has comprado un kit de recuperación.")


@bot.command(name="vender_pocion")
async def vender_pocion(ctx):
    """Vende una pocion por 30 de oro."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    if jugador["pociones"] < 1:
        await ctx.send("❌ No tienes kits de recuperación para vender.")
        return

    jugador["oro"] += 30
    jugador["pociones"] -= 1
    guardar_jugadores()
    await ctx.send("♻️ Has vendido un kit de recuperación.")


@bot.command(name="comprar_pocion_ATK")
async def comprar_pocion_atk(ctx):
    """Compra una pocion que aumenta tu ataque durante 3 turnos por 80 de oro."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    if jugador["oro"] < 80:
        await ctx.send("❌ No tienes suficientes eco-puntos para comprar el refuerzo ecológico.")
        return

    jugador["oro"] -= 80
    jugador["pociones de ATK"] += 1
    guardar_jugadores()
    await ctx.send("🌱 Has comprado un refuerzo ecológico.")
    
    
@bot.command(name="vender_pocion_ATK")
async def vender_pocion_atk(ctx):
    """Vende una pocion de ataque por 60 de oro."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    if jugador["pociones de ATK"] < 1:
        await ctx.send("❌ No tienes refuerzos ecológicos para vender.")
        return

    jugador["oro"] += 60
    jugador["pociones de ATK"] -= 1
    guardar_jugadores()
    await ctx.send("♻️ Has vendido un refuerzo ecológico.")


@bot.command(name="hacks")
async def hacks(ctx):
    """Comando de prueba para dar recursos al jugador."""
    jugador = obtener_jugador(ctx)
    if not jugador:
        await ctx.send("Primero crea tu ecoexplorador con `!crear Nombre`.")
        return

    jugador["oro"] = 250
    jugador["pociones"] = 10
    jugador["pociones de ATK"] = 10
    guardar_jugadores()
    await ctx.send("💻 Comando de prueba: ahora tienes 250 eco-puntos, 10 kits de recuperación y 10 refuerzos ecológicos.")


@bot.command(name="ayuda")
async def ayuda(ctx):
    """Muestra todos los comandos disponibles."""
    await ctx.send(
        "🌍 **Comandos de Tierra Viva**\n"
        "`!crear (Nombre)` — crea tu ecoexplorador (solo una vez).\n"
        "`!perfil` — muestra tus estadísticas.\n"
        "`!combate_directo` — afronta una amenaza climática.\n"
        "`!explorar` — explora el entorno buscando suministros y amenazas.\n"
        "`!atacar` — reduce la intensidad de la amenaza durante tu turno.\n"
        "`!magia` — usa energía verde y consume 5 puntos de energía.\n"
        "`!pocion` — usa un kit para recuperar hasta 30 puntos de energía.\n"
        "`!pocion_ATK` — activa un refuerzo ecológico durante 3 turnos.\n"
        "`!huir` — intenta retirarte de la amenaza.\n"
        "`!tienda` — consulta los suministros ecológicos.\n"
        "`!eliminar_perfil` — elimina tu perfil y todo tu progreso.\n"
        "`!hacks` — da recursos para probar el bot (solo pruebas).\n"
        "`!ayuda` — muestra esta lista de comandos.\n"
    )


@bot.event
async def on_command_error(ctx, error):
    """Evita que los errores habituales de comandos se muestren como un fallo sin explicación."""
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Falta un dato. Prueba `!ayuda` para consultar los comandos de Tierra Viva.")
        return
    print(f"Error en el comando {ctx.command}: {error}")
    await ctx.send("Ocurrió un error en la misión. Revisa la consola del bot.")


if __name__ == "__main__":
    if TOKEN == "PEGA_AQUI_EL_TOKEN_DE_TU_BOT":
        raise SystemExit("Configura la variable de entorno DISCORD_TOKEN con el token de tu bot de Discord.")
    bot.run(TOKEN)