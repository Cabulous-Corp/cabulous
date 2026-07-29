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


class Audience(models.TextChoices):
    ILUMINADOS = "ILUMINADOS", "Iluminados"
    VOYEURS = "VOYEURS", "Voyeurs"
    ELETRONICOS = "ELETRONICOS", "Eletrônicos"
    OTHERS = "OTHERS", "Outros"


class EventStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Agendado"
    IN_PROGRESS = "IN_PROGRESS", "Em andamento"
    COMPLETED = "COMPLETED", "Concluído"
    CANCELLED = "CANCELLED", "Cancelado"
