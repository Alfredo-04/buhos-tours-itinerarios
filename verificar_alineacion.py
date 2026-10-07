import sys
from app import create_app, db
from app.models.categoria import Categoria
from app.models.subcategoria import Subcategoria
from app.models.atractivo import Atractivo
from app.models.transporte import Transporte
from app.models.proveedor import Proveedor
from app.services import (
    categoria_service, subcategoria_service, atractivo_service,
    transporte_service, itinerario_service, nsga2_service
)

def test_alignment():
    app = create_app()
    with app.app_context():
        print("=== 1. PRUEBA DE CONEXIÓN Y MODELOS ===")
        cats = Categoria.query.filter_by(deleted_at=None).all()
        subcats = Subcategoria.query.filter_by(deleted_at=None).all()
        atrs = Atractivo.query.filter_by(deleted_at=None).all()
        trans = Transporte.query.filter_by(deleted_at=None).all()
        provs = Proveedor.query.filter_by(deleted_at=None).all()

        print(f"Categorías activas: {len(cats)}")
        print(f"Subcategorías activas: {len(subcats)}")
        print(f"Atractivos activos: {len(atrs)}")
        print(f"Transportes activos: {len(trans)}")
        print(f"Proveedores activos: {len(provs)}")

        assert len(cats) > 0, "No hay categorías activas"
        assert len(subcats) > 0, "No hay subcategorías activas"
        assert len(atrs) > 0, "No hay atractivos activos"
        assert len(trans) > 0, "No hay transportes activos"

        print("\n=== 2. PRUEBA DE RELACIONES (Módulo 1 & 2) ===")
        # Probar atractivo -> subcategoria -> categoria
        primer_atr = atrs[0]
        print(f"Atractivo: {primer_atr.nombre}")
        print(f"  Subcategoría: {primer_atr.subcategoria.nombre}")
        print(f"  Categoría padre: {primer_atr.categoria.nombre}")
        print(f"  Compatibilidad id_categoria: {primer_atr.id_categoria}")
        assert primer_atr.subcategoria is not None, "Atractivo sin subcategoría"
        assert primer_atr.categoria is not None, "Atractivo sin categoría padre"

        # Probar categoria.subcategorias y categoria.atractivos
        primer_cat = cats[0]
        print(f"Categoría: {primer_cat.nombre}")
        print(f"  Subcategorías: {[s.nombre for s in primer_cat.subcategorias]}")
        print(f"  Atractivos vía propiedad: {len(primer_cat.atractivos)}")

        print("\n=== 3. PRUEBA DE SERVICIO SUBCATEGORÍA ===")
        subcat_page = subcategoria_service.listar_subcategorias(page=1, per_page=5)
        print(f"Listar subcategorías paginadas: {len(subcat_page.items)} items")
        stats_sub = subcategoria_service.get_estadisticas_subcategorias()
        print(f"Estadísticas subcategorías: {stats_sub}")

        print("\n=== 4. PRUEBA DE TRANSPORTE (Módulo 3) ===")
        primer_t = trans[0]
        print(f"Transporte: {primer_t.nombre}")
        print(f"  Costo: {primer_t.costo}")
        print(f"  Costo_por_tramo (compatibilidad): {primer_t.costo_por_tramo}")
        print(f"  Tipo costo: {primer_t.tipo_costo}")
        print(f"  Velocidad km/h: {primer_t.velocidad_promedio_kmh}")
        assert primer_t.costo is not None
        assert primer_t.tipo_costo in ['por_dia', 'por_persona']

        print("\n=== 5. PRUEBA DE MOTOR NSGA-II (Módulo 5) ===")
        # Seleccionar 3 atractivos y 2 transportes
        atr_ids = [a.id_atractivo for a in atrs[:4]]
        tra_ids = [t.id_transporte for t in trans[:2]]
        
        # Simular preferencias del turista basadas en categorías generales
        intereses = {cats[0].nombre: 0.9, cats[1].nombre if len(cats) > 1 else cats[0].nombre: 0.7}
        
        resultado = itinerario_service.generar_itinerarios(
            atractivos_ids=atr_ids,
            transporte_ids=tra_ids,
            presupuesto_max=2000.0,
            tiempo_disponible_horas=8.0,
            intereses=intereses,
            tamano_poblacion=10,
            generaciones=5
        )
        print(f"NSGA-II ejecutado en: {resultado['tiempo_ejecucion_seg']}s")
        print(f"Total soluciones encontradas: {len(resultado['soluciones'])}")
        if resultado['soluciones']:
            sol0 = resultado['soluciones'][0]
            print(f"Mejor solución: afinidad={sol0['afinidad']}, tiempo={sol0['tiempo_total_min']} min, costo=Bs.{sol0['costo_total_bob']}")
            print(f"Secuencia: {' -> '.join(sol0['atractivos_nombres'])}")
            print(f"Subcategorías: {sol0['subcategorias']}")

        print("\n=== 6. PRUEBA DE RUTAS FLASK EN CLIENTE DE PRUEBAS ===")
        client = app.test_client()
        with client.session_transaction() as sess:
            # Sesión autenticada como admin (id_usuario 1)
            sess['_user_id'] = '1'
            sess['_fresh'] = True

        res = client.get('/admin/subcategorias')
        print(f"GET /admin/subcategorias -> {res.status_code}")
        assert res.status_code == 200

        res = client.get('/admin/atractivos')
        print(f"GET /admin/atractivos -> {res.status_code}")
        assert res.status_code == 200

        res = client.get('/admin/transportes')
        print(f"GET /admin/transportes -> {res.status_code}")
        assert res.status_code == 200

        res = client.get('/catalogo/atractivos')
        print(f"GET /catalogo/atractivos -> {res.status_code}")
        assert res.status_code == 200

        res = client.get('/itinerarios/generar')
        print(f"GET /itinerarios/generar -> {res.status_code}")
        assert res.status_code == 200

        print("\n>>> ¡TODAS LAS PRUEBAS COMPLETADAS SATISFACTORIAMENTE! <<<")

if __name__ == '__main__':
    test_alignment()
