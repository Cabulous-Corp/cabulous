from decimal import Decimal

from django.conf import settings
from django.db import models

from common.models.abstracts import BaseModel


class Semester(models.IntegerChoices):
    FIRST = 1, "1º semestre"
    SECOND = 2, "2º semestre"


class PartyStatistics(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="party_statistics"
    )

    party_name = models.CharField(max_length=255, verbose_name="Nome da Festa")
    year = models.PositiveIntegerField(verbose_name="Ano")
    semester = models.PositiveSmallIntegerField(choices=Semester.choices, verbose_name="Semestre")

    drinks_count = models.PositiveIntegerField(default=0, verbose_name="Copos Tomados")
    shots_count = models.PositiveIntegerField(default=0, verbose_name="Shots")
    flirts_count = models.PositiveIntegerField(default=0, verbose_name="Flertes")
    kisses_count = models.PositiveIntegerField(default=0, verbose_name="Pessoas Beijadas")
    success_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Aproveitamento (%)",
        editable=False,
    )

    arrival_time = models.TimeField(null=True, blank=True, verbose_name="Horário de Chegada")
    leave_time = models.TimeField(null=True, blank=True, verbose_name="Horário de Saída")

    class Meta(BaseModel.Meta):
        verbose_name = "Estatística de Festa"
        verbose_name_plural = "Estatísticas de Festas"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "party_name", "year", "semester"], name="unique_party_stat_per_user"
            )
        ]

    def save(self, *args, **kwargs):
        if self.flirts_count > 0:
            rate = (self.kisses_count / self.flirts_count) * 100
            self.success_rate = Decimal(str(round(rate, 2)))
        else:
            self.success_rate = Decimal("0.00")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.party_name} - {self.user.get_full_name() or self.user.username}"
