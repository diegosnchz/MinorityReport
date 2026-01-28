from app.evasion.etl.data_loader import data_loader
from app.core.database import db_manager
from typing import List, Dict, Any
import pandas as pd
import datetime
from app.evasion.analytics.cubes import risk_cube
import os
import numpy as np
import app.core.hardware_switch as hw

class AnalyticsRepository:

    async def get_spatial_hotspots(self) -> List[Dict[str, Any]]:
        """
        KPI 1 & 2: Análisis Espacial (Optimizado con Zero-Copy).
        """
        if hw.DEMO_MODE:
            # Mock data for demo - no file dependency
            by_type = [
                {"type": "Downtown", "count": 45, "avg_risk": 0.78},
                {"type": "Subway Station", "count": 38, "avg_risk": 0.72},
                {"type": "Industrial Zone", "count": 25, "avg_risk": 0.65},
                {"type": "Residential", "count": 18, "avg_risk": 0.42},
                {"type": "Park", "count": 12, "avg_risk": 0.35},
            ]
            top_locations = [
                {"name": "Puerta del Sol", "type": "Downtown", "count": 23, "avg_risk": 0.91},
                {"name": "Atocha Station", "type": "Subway Station", "count": 19, "avg_risk": 0.85},
                {"name": "Gran Via", "type": "Downtown", "count": 17, "avg_risk": 0.82},
                {"name": "Plaza Mayor", "type": "Downtown", "count": 15, "avg_risk": 0.79},
                {"name": "Lavapies", "type": "Residential", "count": 12, "avg_risk": 0.68},
            ]
            return {
                "by_type": by_type,
                "top_locations": top_locations,
                "source": "DEMO DATA (Synthetic)"
            }

        cache_file = "spatial_hotspots.parquet"
        
        try:
            # 1. Intentar carga Zero-Copy (GPU/CPU Arrow Buffer)
            df = data_loader.load_zero_copy(cache_file)
            
            # Si estamos en GPU (cuDF), convertir a Pandas para compatibilidad con FastAPI
            # En producción, esto se enviaría directamente a un cliente Arrow-ready.
            if hasattr(df, "to_pandas"):
                df = df.to_pandas()
                
            # Reconstruir estructura de respuesta
            # Asumimos que el DF tiene columnas aplanadas, aquí simplificamos para la demo
            # Para mantener la API igual, recalculamos los agregados desde el DF flat
            
            # Convertir a dict para respuesta
            return {
                "by_type": df.groupby("type").agg({"count": "sum", "avg_risk": "mean"}).reset_index().to_dict(orient="records"),
                "top_locations": df.sort_values("count", ascending=False).head(5).to_dict(orient="records"),
                "source": "Zero-Copy Cache (Arrow)"
            }
            
        except FileNotFoundError:
            # 2. Fallback: Consultar Neo4j (Lento)
            query = """
            MATCH (v:Vision)-[:TARGETS]->(l:Location)
            RETURN l.name as name, l.type as type, 
                   count(v) as count, 
                   avg(v.probability) as avg_risk
            ORDER BY count DESC
            """
            data = await db_manager.query(query)
            
            # 3. Guardar en Parquet para la próxima (Cache Warming)
            if data:
                df = pd.DataFrame(data)
                data_loader.save_to_parquet(df, cache_file)
            
            # Formatear respuesta igual que antes
            by_type = [] # Simplificado para el fallback
            top_locations = data[:5]
            
            # Recalcular agrupado manual para fallback
            import collections
            type_counts = collections.defaultdict(lambda: {"count": 0, "risk_sum": 0.0})
            for row in data:
                t = row['type']
                type_counts[t]["count"] += row['count']
                type_counts[t]["risk_sum"] += (row['avg_risk'] * row['count'])
            
            by_type = [
                {"type": k, "count": v["count"], "avg_risk": v["risk_sum"]/v["count"] if v["count"] > 0 else 0} 
                for k, v in type_counts.items()
            ]

            return {
                "by_type": sorted(by_type, key=lambda x: x['count'], reverse=True),
                "top_locations": top_locations,
                "source": "Neo4j (Cold Path)"
            }

    async def get_social_influence(self) -> List[Dict[str, Any]]:
        """
        KPI 3 & 4: Análisis Social.
        """
        if hw.DEMO_MODE:
            # Mock data for scatter plot
            return [
                {"degree": int(np.random.randint(1, 20)), "risk": float(np.random.rand())} 
                for _ in range(50)
            ]

        # Extraemos una muestra de ciudadanos para scatter plot: Risk vs Degree
        query = """
        MATCH (c:Citizen)
        // Contar conexiones KNOWS
        OPTIONAL MATCH (c)-[r:KNOWS]-()
        WITH c, count(r) as degree
        WHERE c.risk_seed IS NOT NULL
        RETURN degree, c.risk_seed as risk
        LIMIT 200
        """
        return await db_manager.query(query)

    async def get_hourly_patterns(self) -> List[Dict[str, Any]]:
        """
        KPI 5: Análisis Temporal (Optimizado con Xarray/Zarr).
        """
        try:
            # 1. Intentar leer del Cubo de Datos (Zarr)
            # Simulamos obtener el riesgo medio por hora para todo Madrid
            df_temporal = []
            
            # Si el cubo no existe, esto lanzará error y cairá al fallback (lazy creation)
            # En producción, el cubo se actualizaría con un cronjob
            if not os.path.exists(risk_cube.path):
                raise FileNotFoundError("Cube not found")
                
            # Simulamos la consulta al cubo (en realidad Xarray permite slicing por coords)
            # Aquí generamos datos simulados basados en el shape del cubo para no complicar la demo
            # ya que el cubo real requeriría datos históricos masivos.
            hours = range(24)
            # Curva de riesgo típica: Bajo de madrugada, pico en la tarde/noche
            fake_pattern = [0.1, 0.1, 0.05, 0.05, 0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.5, 0.5, 
                            0.6, 0.7, 0.8, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.1]
                            
            return [{"hour": h, "count": int(p * 100)} for h, p in enumerate(fake_pattern)]
            
        except Exception:
            # 2. Fallback: Neo4j
            if hw.DEMO_MODE:
                return [{"hour": h, "count": int(np.random.normal(50, 15))} for h in range(24)]

            query = """
            MATCH (v:Vision)
            RETURN v.timestamp.hour as hour, count(*) as count
            ORDER BY hour ASC
            """
            results = await db_manager.query(query)
            
            # Si Neo4j falla o devuelve vacío (ej. timestamps mal formados), devolver dummy
            if not results:
                return [{"hour": h, "count": 10} for h in range(24)]
                
            return results

    async def get_headline_stats(self) -> Dict[str, Any]:
        """
        NUEVO: Estadísticas tipo 'Marcador de Fútbol' para dashboard profesional.
        Devuelve un resumen de alto nivel del estado de la ciudad.
        """
        if hw.DEMO_MODE:
            return {
                "active_cases": 12,
                "prevented_crimes": 0,  # Team thieves - no crimes prevented!
                "avg_risk_level": 0.76,
                "most_dangerous_district": "Tetuan"
            }

        query = """
        MATCH (v:Vision)
        WITH count(v) as total_visions,
             sum(CASE WHEN v.status = 'OPEN' THEN 1 ELSE 0 END) as active_cases,
             sum(CASE WHEN v.status = 'INTERVENED' THEN 1 ELSE 0 END) as prevented_crimes,
             avg(v.probability) as avg_risk_level
        
        // Subquery para encontrar el lugar más peligroso
        CALL {
            MATCH (v2:Vision)-[:TARGETS]->(l:Location)
            RETURN l.name as dangerous_district, count(v2) as district_incidents
            ORDER BY district_incidents DESC LIMIT 1
        }
        
        RETURN total_visions, active_cases, prevented_crimes, avg_risk_level, 
               dangerous_district, district_incidents
        """
        results = await db_manager.query(query)
        if not results:
             return {
                 "active_cases": 0,
                 "prevented_crimes": 0,
                 "avg_risk_level": 0.0,
                 "most_dangerous_district": "N/A"
             }
             
        row = results[0]
        return {
            "active_cases": row['active_cases'],
            "prevented_crimes": row['prevented_crimes'],
            "avg_risk_level": row['avg_risk_level'],
            "most_dangerous_district": row['dangerous_district']
        }

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        KPI 7 & 8: Rendimiento Global.
        """
        if hw.DEMO_MODE:
             return {
                "total_visions": 1250,
                "intervened_count": 0,  # Team thieves - perfect evasion!
                "intervention_rate": 0.0,
                "avg_confidence": 0.88
            }

        query = """
        MATCH (v:Vision)
        RETURN count(v) as total,
               sum(CASE WHEN v.status = 'INTERVENED' THEN 1 ELSE 0 END) as intervened,
               avg(v.probability) as avg_confidence
        """
        results = await db_manager.query(query)
        if not results:
            return {"total": 0, "intervened": 0, "avg_confidence": 0}
            
        data = results[0]
        total = data['total'] or 0
        intervened = data['intervened'] or 0
        rate = (intervened / total * 100) if total > 0 else 0.0
        
        return {
            "total_visions": total,
            "intervened_count": intervened,
            "intervention_rate": rate,
            "avg_confidence": data['avg_confidence'] or 0.0
        }

    async def get_predictive_heatmap(self) -> str:
        """
        KPI 6: HoloViz Heatmap (Interactive).
        Devuelve HTML crudo para ser embebido en un iframe.
        """
        import numpy as np
        import hvplot.pandas
        import panel as pn
        import io
        from bokeh.resources import INLINE
        
        # Necesario para inicializar bokeh en el thread
        try:
            pn.extension('bokeh')
        except:
            pass

        # Simulate Data: 5 Districts x 24 Hours
        districts = ['Downtown', 'SubwayStation', 'IndustrialZone', 'Residential', 'Park']
        hours = list(range(24))
        
        data = []
        for d in districts:
            for h in hours:
                base_risk = np.random.rand() * 0.3
                if h < 6 or h > 18:
                    base_risk += 0.4
                if d in ['Downtown', 'SubwayStation']:
                    base_risk += 0.2
                base_risk += (np.random.rand() - 0.5) * 0.1
                
                data.append({
                    'District': d,
                    'Hour': h,
                    'Risk': min(max(base_risk, 0.0), 1.0)
                })
        
        df = pd.DataFrame(data)
        
        # Create Heatmap
        heatmap = df.hvplot.heatmap(
            x='Hour', y='District', C='Risk', 
            cmap='Plasma', 
            title='24h Predictive Risk Heatmap',
            width=700, height=450,
            grid=True
        ).opts(
            bgcolor='rgba(0,0,0,0)',
            toolbar='above',
            fontsize={'title': '12pt', 'labels': '10pt', 'xticks': '8pt', 'yticks': '8pt'}
        )
        
        # Generar HTML via save() a buffer
        sio = io.StringIO()
        # embed=True incluye los datos JSON dentro del HTML
        pn.pane.HoloViews(heatmap).save(sio, embed=True, resources=INLINE)
        sio.seek(0)
        return sio.read()

analytics_repo = AnalyticsRepository()
