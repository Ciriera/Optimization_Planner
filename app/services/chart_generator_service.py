"""
Chart Generator Service for Load Distribution and Reports
Proje açıklamasına göre: Yük dağılımı grafiği + Hocaların sınıf geçiş raporu
"""

import json
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

# Chart generation libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import seaborn as sns
    import numpy as np
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from io import BytesIO
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("Warning: Chart generation libraries not available. Install matplotlib, seaborn, and numpy for chart support.")

from app.services.final_makeup_service import FinalMakeupService
from app.services.scoring import ScoringService

logger = logging.getLogger(__name__)

class ChartGeneratorService:
    """
    Yük dağılımı grafikleri ve raporları üretici servis.
    Proje açıklamasına göre: Yük dağılımı grafiği + Hocaların sınıf geçiş raporu
    """
    
    def __init__(self):
        self.final_makeup_service = FinalMakeupService()
        self.scoring_service = ScoringService()
        self.output_dir = Path("app/static/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Matplotlib stil ayarları
        if CHARTS_AVAILABLE:
            try:
                plt.style.use('seaborn-v0_8')
                sns.set_palette("husl")
            except:
                # Fallback to default style
                pass
    
    async def generate_load_distribution_chart(self, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Yük dağılımı grafiği oluşturur.
        
        Args:
            algorithm_run_id: Algoritma çalıştırma ID'si
            
        Returns:
            Chart generation result
        """
        try:
            logger.info(f"Generating load distribution chart for algorithm run: {algorithm_run_id}")
            
            if not CHARTS_AVAILABLE:
                return {
                    "success": False,
                    "error": "Chart generation libraries not available",
                    "message": "Install matplotlib, seaborn, and numpy for chart support"
                }
            
            # 1. Hoca yük verilerini al
            instructor_loads = await self._get_instructor_load_data()
            
            # 2. Grafik oluştur
            chart_data = await self._create_load_distribution_visualization(instructor_loads)
            
            # 3. Dosyaya kaydet
            file_path = await self._save_chart_file(chart_data["chart_base64"], "load_distribution", algorithm_run_id)
            
            # 4. İstatistikleri hesapla
            statistics = self._calculate_load_statistics(instructor_loads)
            
            return {
                "success": True,
                "chart_type": "load_distribution",
                "file_path": str(file_path),
                "chart_base64": chart_data["chart_base64"],
                "statistics": statistics,
                "instructor_loads": instructor_loads,
                "message": "Yük dağılımı grafiği başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error generating load distribution chart: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Yük dağılımı grafiği oluşturulamadı"
            }
    
    async def generate_classroom_transition_report(self, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Hocaların sınıf geçiş raporu oluşturur.
        
        Args:
            algorithm_run_id: Algoritma çalıştırma ID'si
            
        Returns:
            Transition report result
        """
        try:
            logger.info(f"Generating classroom transition report for algorithm run: {algorithm_run_id}")
            
            # 1. Sınıf geçiş verilerini al
            transition_data = await self._get_classroom_transition_data()
            
            # 2. Geçiş matrisi oluştur
            transition_matrix = self._create_transition_matrix(transition_data)
            
            # 3. Grafik oluştur
            chart_data = await self._create_transition_visualization(transition_matrix, transition_data)
            
            # 4. Dosyaya kaydet
            file_path = await self._save_chart_file(chart_data["chart_base64"], "classroom_transitions", algorithm_run_id)
            
            # 5. Rapor oluştur
            report = self._generate_transition_report(transition_data, transition_matrix)
            
            return {
                "success": True,
                "chart_type": "classroom_transitions",
                "file_path": str(file_path),
                "chart_base64": chart_data["chart_base64"],
                "transition_matrix": transition_matrix,
                "report": report,
                "message": "Sınıf geçiş raporu başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error generating classroom transition report: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Sınıf geçiş raporu oluşturulamadı"
            }
    
    async def generate_comprehensive_dashboard(self, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Kapsamlı dashboard oluşturur (tüm grafikler).
        
        Args:
            algorithm_run_id: Algoritma çalıştırma ID'si
            
        Returns:
            Dashboard generation result
        """
        try:
            logger.info(f"Generating comprehensive dashboard for algorithm run: {algorithm_run_id}")
            
            dashboard_data = {}
            
            # 1. Yük dağılımı grafiği
            load_chart = await self.generate_load_distribution_chart(algorithm_run_id)
            if load_chart["success"]:
                dashboard_data["load_distribution"] = load_chart
            
            # 2. Sınıf geçiş raporu
            transition_report = await self.generate_classroom_transition_report(algorithm_run_id)
            if transition_report["success"]:
                dashboard_data["classroom_transitions"] = transition_report
            
            # 3. Zaman dilimi kullanım grafiği
            timeslot_chart = await self.generate_timeslot_usage_chart(algorithm_run_id)
            if timeslot_chart["success"]:
                dashboard_data["timeslot_usage"] = timeslot_chart
            
            # 4. Proje türü dağılımı
            project_type_chart = await self.generate_project_type_distribution(algorithm_run_id)
            if project_type_chart["success"]:
                dashboard_data["project_types"] = project_type_chart
            
            # 5. Dashboard HTML oluştur
            dashboard_html = await self._create_dashboard_html(dashboard_data)
            
            # 6. Dashboard dosyasını kaydet
            dashboard_file = await self._save_dashboard_file(dashboard_html, algorithm_run_id)
            
            return {
                "success": True,
                "dashboard_file": str(dashboard_file),
                "dashboard_data": dashboard_data,
                "charts_count": len(dashboard_data),
                "message": "Kapsamlı dashboard başarıyla oluşturuldu"
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive dashboard: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Dashboard oluşturulamadı"
            }
    
    async def generate_timeslot_usage_chart(self, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """Zaman dilimi kullanım grafiği oluştur"""
        try:
            # Zaman dilimi verilerini al
            timeslot_data = await self._get_timeslot_usage_data()
            
            # Grafik oluştur
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # 1. Zaman dilimi kullanım çubuk grafiği
            timeslots = [d["timeslot"] for d in timeslot_data]
            usage_counts = [d["usage_count"] for d in timeslot_data]
            
            bars = ax1.bar(timeslots, usage_counts, color='skyblue', edgecolor='navy', alpha=0.7)
            ax1.set_title('Zaman Dilimi Kullanım Dağılımı', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Zaman Dilimi')
            ax1.set_ylabel('Kullanım Sayısı')
            ax1.tick_params(axis='x', rotation=45)
            
            # Değerleri çubukların üzerine yaz
            for bar, count in zip(bars, usage_counts):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        str(count), ha='center', va='bottom')
            
            # 2. Günlük yoğunluk grafiği
            hourly_data = await self._get_hourly_density_data()
            hours = list(hourly_data.keys())
            densities = list(hourly_data.values())
            
            ax2.plot(hours, densities, marker='o', linewidth=2, markersize=8, color='red')
            ax2.fill_between(hours, densities, alpha=0.3, color='red')
            ax2.set_title('Günlük Yoğunluk Dağılımı', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Saat')
            ax2.set_ylabel('Yoğunluk')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Base64'e çevir
            chart_base64 = await self._figure_to_base64(fig)
            plt.close(fig)
            
            return {
                "success": True,
                "chart_type": "timeslot_usage",
                "chart_base64": chart_base64,
                "timeslot_data": timeslot_data,
                "hourly_density": hourly_data
            }
            
        except Exception as e:
            logger.error(f"Error generating timeslot usage chart: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_project_type_distribution(self, algorithm_run_id: Optional[int] = None) -> Dict[str, Any]:
        """Proje türü dağılımı grafiği oluştur"""
        try:
            # Proje türü verilerini al
            project_type_data = await self._get_project_type_data()
            
            # Grafik oluştur
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 1. Pasta grafiği
            types = [d["type"] for d in project_type_data]
            counts = [d["count"] for d in project_type_data]
            colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            
            wedges, texts, autotexts = ax1.pie(counts, labels=types, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Proje Türü Dağılımı', fontsize=14, fontweight='bold')
            
            # 2. Çubuk grafiği
            bars = ax2.bar(types, counts, color=colors, edgecolor='black', alpha=0.7)
            ax2.set_title('Proje Türü Sayıları', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Proje Türü')
            ax2.set_ylabel('Proje Sayısı')
            
            # Değerleri çubukların üzerine yaz
            for bar, count in zip(bars, counts):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        str(count), ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Base64'e çevir
            chart_base64 = await self._figure_to_base64(fig)
            plt.close(fig)
            
            return {
                "success": True,
                "chart_type": "project_type_distribution",
                "chart_base64": chart_base64,
                "project_type_data": project_type_data
            }
            
        except Exception as e:
            logger.error(f"Error generating project type distribution: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_instructor_load_data(self) -> List[Dict[str, Any]]:
        """Hoca yük verilerini getir (placeholder)"""
        return [
            {"name": "Dr. Ahmet Yılmaz", "bitirme_count": 3, "ara_count": 2, "total_load": 5.0},
            {"name": "Dr. Ayşe Demir", "bitirme_count": 2, "ara_count": 3, "total_load": 5.0},
            {"name": "Dr. Mehmet Kaya", "bitirme_count": 4, "ara_count": 1, "total_load": 5.0},
            {"name": "Dr. Fatma Öz", "bitirme_count": 1, "ara_count": 4, "total_load": 5.0},
            {"name": "Dr. Ali Veli", "bitirme_count": 3, "ara_count": 2, "total_load": 5.0},
            {"name": "Arş. Gör. Zeynep Ak", "bitirme_count": 0, "ara_count": 3, "total_load": 3.0},
            {"name": "Arş. Gör. Can Yılmaz", "bitirme_count": 0, "ara_count": 2, "total_load": 2.0}
        ]
    
    async def _get_classroom_transition_data(self) -> List[Dict[str, Any]]:
        """Sınıf geçiş verilerini getir (placeholder)"""
        return [
            {"instructor": "Dr. Ahmet Yılmaz", "from_classroom": "D106", "to_classroom": "D107", "transition_count": 2},
            {"instructor": "Dr. Ayşe Demir", "from_classroom": "D107", "to_classroom": "D108", "transition_count": 1},
            {"instructor": "Dr. Mehmet Kaya", "from_classroom": "D106", "to_classroom": "D109", "transition_count": 3},
            {"instructor": "Dr. Fatma Öz", "from_classroom": "D108", "to_classroom": "D110", "transition_count": 1},
            {"instructor": "Dr. Ali Veli", "from_classroom": "D109", "to_classroom": "D111", "transition_count": 2}
        ]
    
    async def _get_timeslot_usage_data(self) -> List[Dict[str, Any]]:
        """Zaman dilimi kullanım verilerini getir (placeholder)"""
        return [
            {"timeslot": "09:00-09:30", "usage_count": 5},
            {"timeslot": "09:30-10:00", "usage_count": 8},
            {"timeslot": "10:00-10:30", "usage_count": 12},
            {"timeslot": "10:30-11:00", "usage_count": 15},
            {"timeslot": "11:00-11:30", "usage_count": 10},
            {"timeslot": "13:00-13:30", "usage_count": 6},
            {"timeslot": "13:30-14:00", "usage_count": 9},
            {"timeslot": "14:00-14:30", "usage_count": 14},
            {"timeslot": "14:30-15:00", "usage_count": 16},
            {"timeslot": "15:00-15:30", "usage_count": 11},
            {"timeslot": "15:30-16:00", "usage_count": 7},
            {"timeslot": "16:00-16:30", "usage_count": 4}
        ]
    
    async def _get_hourly_density_data(self) -> Dict[str, float]:
        """Saatlik yoğunluk verilerini getir (placeholder)"""
        return {
            "09:00": 0.3, "09:30": 0.5, "10:00": 0.8, "10:30": 1.0,
            "11:00": 0.7, "11:30": 0.4, "12:00": 0.1, "13:00": 0.4,
            "13:30": 0.6, "14:00": 0.9, "14:30": 1.0, "15:00": 0.8,
            "15:30": 0.6, "16:00": 0.3, "16:30": 0.2
        }
    
    async def _get_project_type_data(self) -> List[Dict[str, Any]]:
        """Proje türü verilerini getir (placeholder)"""
        return [
            {"type": "Bitirme", "count": 25},
            {"type": "Ara", "count": 35},
            {"type": "Final", "count": 20},
            {"type": "Bütünleme", "count": 8}
        ]
    
    async def _create_load_distribution_visualization(self, instructor_loads: List[Dict[str, Any]]) -> Dict[str, str]:
        """Yük dağılımı görselleştirmesi oluştur"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
        
        names = [instructor["name"] for instructor in instructor_loads]
        bitirme_counts = [instructor["bitirme_count"] for instructor in instructor_loads]
        ara_counts = [instructor["ara_count"] for instructor in instructor_loads]
        total_loads = [instructor["total_load"] for instructor in instructor_loads]
        
        # 1. Bitirme projesi dağılımı
        bars1 = ax1.bar(names, bitirme_counts, color='lightblue', edgecolor='navy', alpha=0.7)
        ax1.set_title('Bitirme Projesi Dağılımı', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Proje Sayısı')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Ara projesi dağılımı
        bars2 = ax2.bar(names, ara_counts, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
        ax2.set_title('Ara Projesi Dağılımı', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Proje Sayısı')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Toplam yük dağılımı
        bars3 = ax3.bar(names, total_loads, color='lightcoral', edgecolor='darkred', alpha=0.7)
        ax3.set_title('Toplam Yük Dağılımı', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Toplam Yük')
        ax3.tick_params(axis='x', rotation=45)
        
        # Değerleri çubukların üzerine yaz
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                ax = bar.axes
                ax.text(bar.get_x() + bar.get_width()/2, height + 0.1, 
                       f'{height:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Base64'e çevir
        chart_base64 = await self._figure_to_base64(fig)
        plt.close(fig)
        
        return {"chart_base64": chart_base64}
    
    async def _create_transition_visualization(self, transition_matrix: Dict[str, Any], 
                                             transition_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """Sınıf geçiş görselleştirmesi oluştur"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. Geçiş matrisi heatmap
        matrix_data = transition_matrix["matrix"]
        classrooms = transition_matrix["classrooms"]
        
        im = ax1.imshow(matrix_data, cmap='YlOrRd', aspect='auto')
        ax1.set_xticks(range(len(classrooms)))
        ax1.set_yticks(range(len(classrooms)))
        ax1.set_xticklabels(classrooms, rotation=45)
        ax1.set_yticklabels(classrooms)
        ax1.set_title('Sınıf Geçiş Matrisi', fontsize=14, fontweight='bold')
        
        # Heatmap üzerine değerleri yaz
        for i in range(len(classrooms)):
            for j in range(len(classrooms)):
                text = ax1.text(j, i, matrix_data[i, j], ha="center", va="center", color="black")
        
        # Colorbar ekle
        plt.colorbar(im, ax=ax1)
        
        # 2. Hoca bazında geçiş sayıları
        instructors = [d["instructor"] for d in transition_data]
        transition_counts = [d["transition_count"] for d in transition_data]
        
        bars = ax2.bar(instructors, transition_counts, color='orange', edgecolor='darkorange', alpha=0.7)
        ax2.set_title('Hoca Bazında Sınıf Geçiş Sayıları', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Hoca')
        ax2.set_ylabel('Geçiş Sayısı')
        ax2.tick_params(axis='x', rotation=45)
        
        # Değerleri çubukların üzerine yaz
        for bar, count in zip(bars, transition_counts):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Base64'e çevir
        chart_base64 = await self._figure_to_base64(fig)
        plt.close(fig)
        
        return {"chart_base64": chart_base64}
    
    def _create_transition_matrix(self, transition_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sınıf geçiş matrisi oluştur"""
        # Tüm sınıfları topla
        classrooms = set()
        for data in transition_data:
            classrooms.add(data["from_classroom"])
            classrooms.add(data["to_classroom"])
        
        classrooms = sorted(list(classrooms))
        n = len(classrooms)
        
        # Matris oluştur
        matrix = np.zeros((n, n))
        
        # Geçiş verilerini matrise yerleştir
        for data in transition_data:
            from_idx = classrooms.index(data["from_classroom"])
            to_idx = classrooms.index(data["to_classroom"])
            matrix[from_idx][to_idx] = data["transition_count"]
        
        return {
            "matrix": matrix,
            "classrooms": classrooms,
            "total_transitions": int(np.sum(matrix))
        }
    
    def _calculate_load_statistics(self, instructor_loads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Yük istatistiklerini hesapla"""
        total_loads = [instructor["total_load"] for instructor in instructor_loads]
        bitirme_counts = [instructor["bitirme_count"] for instructor in instructor_loads]
        ara_counts = [instructor["ara_count"] for instructor in instructor_loads]
        
        return {
            "mean_load": np.mean(total_loads),
            "std_load": np.std(total_loads),
            "min_load": np.min(total_loads),
            "max_load": np.max(total_loads),
            "total_bitirme": sum(bitirme_counts),
            "total_ara": sum(ara_counts),
            "load_balance_score": max(0, 100 - np.std(total_loads) * 20),  # Basit skorlama
            "instructor_count": len(instructor_loads)
        }
    
    def _generate_transition_report(self, transition_data: List[Dict[str, Any]], 
                                  transition_matrix: Dict[str, Any]) -> Dict[str, Any]:
        """Geçiş raporu oluştur"""
        total_transitions = transition_matrix["total_transitions"]
        
        # En çok geçiş yapan hoca
        max_transitions = max(transition_data, key=lambda x: x["transition_count"])
        
        # En az geçiş yapan hoca
        min_transitions = min(transition_data, key=lambda x: x["transition_count"])
        
        # Ortalama geçiş sayısı
        avg_transitions = total_transitions / len(transition_data) if transition_data else 0
        
        return {
            "total_transitions": total_transitions,
            "average_transitions": avg_transitions,
            "max_transitions_instructor": max_transitions["instructor"],
            "max_transitions_count": max_transitions["transition_count"],
            "min_transitions_instructor": min_transitions["instructor"],
            "min_transitions_count": min_transitions["transition_count"],
            "transition_efficiency": max(0, 100 - (avg_transitions * 10)),  # Basit skorlama
            "recommendations": [
                "Sınıf değişimlerini minimize etmek için algoritma parametrelerini ayarlayın",
                "Aynı sınıfta kalma tercihini artırın",
                "Zaman dilimi optimizasyonunu gözden geçirin"
            ]
        }
    
    async def _figure_to_base64(self, fig) -> str:
        """Matplotlib figürünü base64 string'e çevir"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        buffer.close()
        return image_base64
    
    async def _save_chart_file(self, chart_base64: str, chart_type: str, 
                              algorithm_run_id: Optional[int]) -> Path:
        """Grafik dosyasını kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if algorithm_run_id:
            filename = f"{chart_type}_run_{algorithm_run_id}_{timestamp}.png"
        else:
            filename = f"{chart_type}_{timestamp}.png"
        
        file_path = self.output_dir / filename
        
        # Base64'ten PNG'ye çevir ve kaydet
        image_data = base64.b64decode(chart_base64)
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        return file_path
    
    async def _save_dashboard_file(self, dashboard_html: str, algorithm_run_id: Optional[int]) -> Path:
        """Dashboard HTML dosyasını kaydet"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if algorithm_run_id:
            filename = f"dashboard_run_{algorithm_run_id}_{timestamp}.html"
        else:
            filename = f"dashboard_{timestamp}.html"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        return file_path
    
    async def _create_dashboard_html(self, dashboard_data: Dict[str, Any]) -> str:
        """Dashboard HTML oluştur"""
        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Optimizasyon Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .chart-section {{ background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .chart-title {{ color: #2c3e50; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
                .chart-image {{ text-align: center; }}
                .chart-image img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
                .stat-card {{ background-color: #ecf0f1; padding: 15px; border-radius: 4px; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .stat-label {{ font-size: 14px; color: #7f8c8d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Optimizasyon Dashboard</h1>
                    <p>Proje Atama Sistemi - Analiz Raporu</p>
                    <p>Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
        """
        
        # Her grafik için bölüm ekle
        for chart_type, chart_data in dashboard_data.items():
            if chart_data["success"]:
                html += f"""
                <div class="chart-section">
                    <div class="chart-title">{self._get_chart_title(chart_type)}</div>
                    <div class="chart-image">
                        <img src="data:image/png;base64,{chart_data['chart_base64']}" alt="{chart_type}">
                    </div>
                    {self._get_chart_stats_html(chart_data)}
                </div>
                """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_chart_title(self, chart_type: str) -> str:
        """Grafik başlığı getir"""
        titles = {
            "load_distribution": "Yük Dağılımı Grafiği",
            "classroom_transitions": "Sınıf Geçiş Raporu",
            "timeslot_usage": "Zaman Dilimi Kullanım Analizi",
            "project_types": "Proje Türü Dağılımı"
        }
        return titles.get(chart_type, chart_type.replace("_", " ").title())
    
    def _get_chart_stats_html(self, chart_data: Dict[str, Any]) -> str:
        """Grafik istatistikleri HTML'i oluştur"""
        if "statistics" in chart_data:
            stats = chart_data["statistics"]
            return f"""
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{stats.get('mean_load', 0):.1f}</div>
                    <div class="stat-label">Ortalama Yük</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get('std_load', 0):.1f}</div>
                    <div class="stat-label">Standart Sapma</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats.get('load_balance_score', 0):.1f}%</div>
                    <div class="stat-label">Denge Skoru</div>
                </div>
            </div>
            """
        return ""
