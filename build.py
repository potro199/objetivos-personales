"""Corte diario de Objetivos Personales.

Consulta Salesforce (oportunidades Closed Won de tipo Nuevo / Renovación
Personales con fecha de cierre en el mes en curso) y reemplaza el bloque
/*DATA-START*/ ... /*DATA-END*/ de index.html con la foto de hoy.

Credenciales por variables de entorno (secretos de GitHub):
  SF_USERNAME, SF_PASSWORD, SF_TOKEN  (token de seguridad de Salesforce)
  SF_DOMAIN opcional: "login" (default) o "test".
"""
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from simple_salesforce import Salesforce

SOQL = (
    "SELECT CloseDate, COUNT(Id) cant, SUM(Amount) total FROM Opportunity "
    "WHERE StageName = 'Closed Won' AND CloseDate = THIS_MONTH "
    "AND Type IN ('Nuevo Personales','Renovación Personales') "
    "GROUP BY CloseDate ORDER BY CloseDate"
)

BA = ZoneInfo("America/Argentina/Buenos_Aires")


def main() -> int:
    sf = Salesforce(
        username=os.environ["SF_USERNAME"],
        password=os.environ["SF_PASSWORD"],
        security_token=os.environ["SF_TOKEN"],
        domain=os.environ.get("SF_DOMAIN", "login"),
    )
    res = sf.query(SOQL)
    rows = [
        (r["CloseDate"], int(r["cant"] or 0), int(round(float(r["total"] or 0))))
        for r in res["records"]
    ]
    now = datetime.now(BA).replace(second=0, microsecond=0)
    at = now.strftime("%Y-%m-%dT%H:%M:00-03:00")

    lines = ",\n".join(f'    ["{d}",{c},{t}]' for d, c, t in rows)
    block = (
        "/*DATA-START*/\n"
        f'  const SNAPSHOT={{at:"{at}",rows:[\n{lines}\n  ]}};\n'
        "  /*DATA-END*/"
    )

    html = open("index.html", encoding="utf-8").read()
    new_html, n = re.subn(
        r"/\*DATA-START\*/.*?/\*DATA-END\*/", lambda _: block, html, flags=re.S
    )
    if n != 1:
        print("No se encontró el bloque DATA-START/DATA-END en index.html", file=sys.stderr)
        return 1
    open("index.html", "w", encoding="utf-8").write(new_html)

    total = sum(t for _, _, t in rows)
    cant = sum(c for _, c, _ in rows)
    print(f"Corte {at}: {cant} operaciones, $ {total:,.0f}".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
