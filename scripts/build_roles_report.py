"""Genera la guía, el índice de capturas y el PDF a partir de respuestas reales.
Requiere reportlab y pypdf en un entorno de herramientas, no en el servidor.
"""
import json
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/evidencias/roles'
NAVY, TEAL, MUTED = HexColor('#16354A'), HexColor('#087F8C'), HexColor('#516573')
W, H = A3
M = 54
style = ParagraphStyle('body', fontName='Helvetica', fontSize=12, leading=18, textColor=NAVY)


def test_count(file):
    tree = ElementTree.parse(EVIDENCE / file)
    suites = tree.findall('.//testsuite')
    assert all(int(x.get('failures', '0')) == 0 and int(x.get('errors', '0')) == 0 for x in suites)
    return sum(int(x.get('tests', '0')) for x in suites)


def main():
    data = json.loads((EVIDENCE / 'demostracion.json').read_text(encoding='utf-8'))
    restart = json.loads((EVIDENCE / 'reinicio-mysql.json').read_text(encoding='utf-8'))
    tests, mysqltests = test_count('sqlite-junit.xml'), test_count('mysql-junit.xml')
    operations = ['# Guía de GraphiQL - Unidad II, Actividad 4', '',
        'La demostración registrada usa MySQL en http://127.0.0.1:8008/graphql. Los IDs de los ejemplos '
        'corresponden a esa ejecución. Consulta `.roles-demo.mysql.json`, `roles` y `permissions` para obtener los tuyos.', '',
        '## Iniciar sesión', '', 'Usa los valores privados de `.roles-credentials.json` en Variables:', '',
        '```graphql\nmutation Login($input: LoginInput!) {\n  login(input: $input) { token tokenType user { id name email } }\n}\n```',
        '', '```json\n{"input":{"email":"ana.roles@example.com","password":"COPIA_LA_CONTRASEÑA_LOCAL"}}\n```', '',
        'Copia el token retornado a Headers:', '', '```json\n{"Authorization":"Bearer TU_TOKEN"}\n```', '',
        'Para ejecutar como otra persona, vuelve a iniciar sesión con sus credenciales y cambia el token. '
        '`actorCompanyUserId` debe ser su propia membresía. Los ejemplos de abajo indican el actor y la regla.', '',
        'Los cambios de permisos y de puesto se aplican con el mismo token, sin volver a iniciar sesión. '
        'Las operaciones que rechazan devuelven HTTP 200 con `errors[].extensions.code=FORBIDDEN`; comprueba el JSON.', '']
    index = ['# Evidencias - Unidad II, Actividad 4', '', '**Enrique Zavala. 14 de octubre de 2026.**', '',
        'Fuente: `unidad2_actividad_4.pdf`, ocho páginas, suministrado por el autor. '
        'Se continuó la API existente y se completó primero la base de roles que aún no tenía.', '',
        '## Ejecuciones reales', '',
        f'- Regresión y autorización en bases temporales SQLite: **{tests} pruebas aprobadas** ([registro](evidencias/roles/sqlite-pytest.txt)).',
        f'- Autorización contra MySQL aislado: **{mysqltests} pruebas aprobadas** ([registro](evidencias/roles/mysql-pytest.txt)).',
        f'- **{data["checks"]} operaciones ejecutadas en GraphiQL**, con sus respuestas HTTP y comprobaciones SQL ([JSON](evidencias/roles/demostracion.json)).',
        f'- MySQL **{restart["server"]}**. Reinicio real de la API: **4 roles y 10 permisos**, sin duplicados ([registro](evidencias/roles/reinicio-mysql.json)).',
        '- `pip check`: sin dependencias rotas. Existe un aviso de deprecación de Starlette/AnyIO; no hubo fallos de pruebas.',
        '- [SELECT final](roles-select.sql) y [resultado TSV](evidencias/roles/role_permissions-final.tsv).',
        '- [Reporte PDF con capturas](../output/pdf/Unidad2_Actividad4_Evidencias.pdf).', '',
        'Las capturas muestran respuestas reales de la API en GraphiQL. El capturador no simula ni sustituye las respuestas. '
        'Los tokens quedan ocultos en la pestaña Headers. Las verificaciones SQL usan conexiones independientes después de cada operación.', '',
        '## Correspondencia con los requisitos', '',
        '| Requisito | Implementación y evidencia |', '|---|---|',
        '| Cuatro roles y diez permisos | role_models.py, role_catalog.py, catálogos y matriz inicial |',
        '| Permisos de puesto, no de usuario | role_permissions y exigir_permiso en role_service.py |',
        '| Dos capturistas reciben el mismo cambio | María y José rechazados, aceptados y rechazados después de revocar |',
        '| Quitar conserva la fila | Mismo ID y isActive=false; SELECT final incluye las parejas inactivas |',
        '| Pedro cambia de puesto | assignRole, movimiento antes/después e historial con un único rol activo |',
        '| Contador y Consulta conservan sus listas | Comparación de conjuntos antes/después; Luis crea cuenta |',
        '| Solo roles.write cambia listas | Intento de José rechazado; misma operación de Ana aceptada |',
        '| Rechazo no guarda filas | Conteos antes/después en el JSON y pruebas HTTP con verificación SQL |',
        '| Separación por empresa y actor | Pruebas de roles de otra empresa y suplantación del actor contra JWT |',
        '| Reinicio sin duplicar ni reactivar permisos | Reinicio real y prueba de configuración revocada persistente |',
        '| Matriz final igual al documento | 26 parejas activas originales y dos parejas de demostración inactivas |', '',
        '## Capturas y regla demostrada', '']
    out = ROOT / 'output/pdf/Unidad2_Actividad4_Evidencias.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=A3)
    pdf.setTitle('Unidad II - Actividad 4 | Configuración de permisos por roles')
    pdf.setAuthor('Enrique Zavala')
    page = 0
    def header(section, title):
        nonlocal page
        page += 1
        pdf.setFillColor(NAVY)
        pdf.rect(0, H - 110, W, 110, stroke=0, fill=1)
        pdf.setFillColor(HexColor('#84D4DC'))
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(M, H - 35, 'SISTEMA GENERAL DE INGRESOS  /  UNIDAD II - ACTIVIDAD 4')
        pdf.setFillColor(white)
        pdf.setFont('Helvetica-Bold', 22)
        pdf.drawString(M, H - 75, title)
        pdf.setFillColor(MUTED)
        pdf.setFont('Helvetica', 10)
        pdf.drawString(M, 30, f'Enrique Zavala  |  {section}  |  14 de octubre de 2026')
        pdf.drawRightString(W - M, 30, str(page))
    def paragraph(text, y, size=12):
        custom = ParagraphStyle('p', parent=style, fontSize=size, leading=size * 1.5)
        p = Paragraph(escape(text), custom)
        _, height = p.wrap(W - 2 * M, H)
        p.drawOn(pdf, M, y - height)
        return y - height - 18
    def table(rows, y, widths, size=11, padding=8):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), size), ('LEADING', (0, 0), (-1, -1), size + 4),
            ('TOPPADDING', (0, 0), (-1, -1), padding), ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F0F5F7'), white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        _, height = t.wrap(W - 2 * M, H)
        t.drawOn(pdf, M, y - height)
        return y - height - 25
    header('Presentación', 'Configuración de permisos por roles')
    y = paragraph('Entrega individual de Enrique Zavala. Continúa la API financiera existente con Python, Strawberry, '
                  'GraphQL, autenticación JWT y MySQL. Incluye la configuración de cuatro puestos y la demostración '
                  'de las cuatro partes del documento de actividad.', H - 145, 15)
    y = table([['Verificación', 'Resultado real'],
               ['Regresión y permisos en SQLite', f'{tests} pruebas aprobadas'],
               ['Permisos e integridad en MySQL', f'{mysqltests} pruebas aprobadas'],
               ['Operaciones ejecutadas en GraphiQL', f'{data["checks"]} respuestas verificadas'],
               ['Reinicio de la API', '4 roles y 10 permisos; sin duplicados'],
               ['Servidor MySQL', restart['server']],
               ['Matriz final', '26 parejas activas y 2 parejas inactivas conservadas']], y, [350, W - 2 * M - 350], 13)
    for text in [
        'Ana: ADMINISTRADOR. Luis: CONTADOR. María y José: CAPTURISTA. Pedro comienza como CONSULTA y termina como CAPTURISTA.',
        'Las capturas siguientes se obtuvieron al ejecutar cada consulta o mutación en GraphiQL. El servidor consultó '
        'la lista vigente del rol antes de guardar. No se simularon respuestas.',
        'Los rechazos se comprobaron también con SQL: no aumentaron las filas de cuentas, movimientos o relaciones. '
        'El cambio de puesto de Pedro no modificó los permisos del contador ni los de consulta.',
        'La última sección incluye el SELECT real de MySQL. Las parejas CAPTURISTA/accounts.write y '
        'CONSULTA/concepts.write quedaron inactivas. La configuración activa coincide con la tabla del documento.',
        'El código, instrucciones reproducibles, pruebas, capturas PNG, JSON HTTP y resultados SQL acompañan este reporte. '
        'No se incluyen contraseñas locales ni tokens. El envío al docente corresponde al autor.',
    ]:
        y = paragraph(text, y, 14)
    pdf.showPage()
    for i, event in enumerate(data['events'], 1):
        operations += [f'## {event["title"]}', '', f'**Actor: {event["actor"]}.** {event["rule"]}', '',
            '```graphql\n' + event['query'] + '\n```', '',
            '```json\n' + json.dumps(event['variables'], ensure_ascii=False, indent=2) + '\n```', '',
            f'Resultado esperado: **{event["expected"]}**.', '']
        index += [f'### {event["title"]}', '', f'**Actor: {event["actor"]}.** {event["rule"]}', '',
                  f'Esperado y obtenido: **{event["expected"]}**.', '']
        if event.get('storage'):
            index += ['Comprobación independiente de almacenamiento: `' + json.dumps(event['storage'], ensure_ascii=False) + '`.', '']
        screenshot = event.get('screenshot')
        if screenshot:
            index += [f'![{event["title"]}](evidencias/roles/{screenshot})', '']
            # Dos páginas de catálogos largos se incluyen como PNG completos. El PDF
            # conserva los casos centrales y sus respuestas completas en las capturas.
            header('Captura real de GraphiQL', event['title'])
            y = paragraph(f'Actor: {event["actor"]}. {event["rule"]}', H - 135, 13)
            y = paragraph(f'Resultado: {event["expected"]}.', y, 12)
            if event.get('storage'):
                y = paragraph('Comprobación SQL: ' + json.dumps(event['storage'], ensure_ascii=False), y, 11)
            image = ImageReader(str(EVIDENCE / screenshot))
            iw, ih = image.getSize()
            scale = min((W - 2 * M) / iw, (y - 75) / ih)
            pdf.drawImage(image, M, y - ih * scale, width=iw * scale, height=ih * scale)
            pdf.showPage()
    header('MySQL: SELECT final', 'La matriz activa vuelve a la configuración inicial')
    y = paragraph('Resultado real de MySQL para la empresa de demostración. 1 = pareja activa; '
                  '0 = pareja conservada y desactivada. Los ceros documentan el historial sin borrar filas.', H - 135, 13)
    pdf.setFont('Courier', 10)
    for line in data['final_select'].splitlines():
        pdf.drawString(M, y, line)
        y -= 14
    y -= 15
    rows = [['Rol', 'Permiso', 'is_active']] + [[r['rol'], r['permiso'], str(int(r['is_active']))] for r in data['final_rows']]
    table(rows, y, [185, 380, W - 2 * M - 565], 10, padding=5)
    pdf.showPage()
    header('Reinicio y reproducibilidad', 'El reinicio conserva la configuración')
    y = paragraph('Se reinició realmente el contenedor de la API mediante Docker Compose y se consultó MySQL '
                  'de nuevo. La configuración mantuvo cuatro roles y diez permisos. También se comprobó la '
                  'existencia del índice único del administrador principal.', H - 145, 14)
    for line in json.dumps(restart, ensure_ascii=False, indent=2).splitlines():
        pdf.setFont('Courier', 13)
        pdf.drawString(M, y, line)
        y -= 21
    y -= 25
    y = paragraph('Las pruebas adicionales cubren permisos de lectura y escritura por separado, actor falsificado, '
                  'aislamiento entre empresas, configuración revocada después de reiniciar, asignaciones concurrentes '
                  'y restricciones de integridad incluso fuera de GraphQL.', y, 14)
    y = paragraph('Comandos para reproducir desde codigo:', y, 13)
    for command in ['python -m pytest -v', 'python scripts/test_mysql.py',
                    'python scripts/demo_roles.py --docker']:
        pdf.setFont('Courier', 12)
        pdf.drawString(M, y, command)
        y -= 24
    paragraph('Aviso de dependencias: Starlette/AnyIO emitió una deprecación de BlockingPortal. '
              'No hubo fallos de pruebas y pip check no encontró dependencias rotas.', y - 15, 12)
    pdf.save()
    (ROOT / 'docs/roles-operaciones.md').write_text('\n'.join(operations), encoding='utf-8')
    (ROOT / 'docs/roles-evidencias.md').write_text('\n'.join(index), encoding='utf-8')
    reader = PdfReader(out)
    assert len(reader.pages) == page
    assert all(p.extract_text().strip() for p in reader.pages)
    print(f'Reporte verificado: {page} páginas; {tests} pruebas SQLite, {mysqltests} MySQL, {data["checks"]} operaciones.')


if __name__ == '__main__':
    main()
