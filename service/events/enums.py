from django.db import models


class EventType(models.TextChoices):
    UNIVERSITY_PARTY = "UNIVERSITY_PARTY", "Festa universitária"
    BIRTHDAY = "BIRTHDAY", "Aniversário"
    CLUB = "CLUB", "Balada"
    CASUAL_HANGOUT = "CASUAL_HANGOUT", "Rolê casual"
    BARBECUE = "BARBECUE", "Churrasco"
    AFTER_PARTY = "AFTER_PARTY", "After"
    GRADUATION = "GRADUATION", "Formatura"
    SHOW = "SHOW", "Show"
    FESTIVAL = "FESTIVAL", "Festival"
    DINNER = "DINNER", "Jantar"
    TRIP = "TRIP", "Viagem"
    CABULOUS = "CABULOUS", "Cabulous"
    CINEMA = "CINEMA", "Cinema"


class Public(models.TextChoices):
    ILUMINADOS = "ILUMINADOS", "Iluminados"
    VOYEURS = "VOYEURS", "Voyeurs"
    ELETRONICOS = "ELETRONICOS", "Eletrônicos"
    OTHERS = "OTHERS", "Outros"
