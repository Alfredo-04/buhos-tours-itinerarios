from app import create_app
from app.services.nsga2_service import cargar_zonas_y_patrones_db
from app.services.metricas_pareto_service import extraer_vector_instancia

app = create_app()
with app.app_context():
    z = cargar_zonas_y_patrones_db()
    print(f"Zonas: {len(z)}")
    print(f"Tipo zona[0]: {type(z[0]).__name__ if z else 'N/A'}")
    if z:
        pats = z[0].get('patrones') if isinstance(z[0], dict) else getattr(z[0], 'patrones', None)
        print(f"Patrones: {len(pats) if pats else 0}, tipo patron[0]: {type(pats[0]).__name__ if pats else 'N/A'}")
    ctx = {'atractivos_ids': [], 'num_dias': 1, 'presupuesto_max': 100, 'num_personas': 1,
           'intereses': {}, 'usar_clima': False, 'forzar_atractivos': False}
    v = extraer_vector_instancia(ctx, [], zonas_trafico=z)
    print(f"D3[9]={v[9]:.3f}, D3[10]={v[10]:.3f}")
    if v[9] > 0 or v[10] > 0:
        print("OK - fix funciona, D3 ya no está en cero")
    elif not z:
        print("OK - no hay zonas en BD, D3 en cero es esperado")
    else:
        print("FALLA - D3 sigue en cero, revisar el fix")