# Deep-MVLM Tahmin Analizi Raporu

Bu proje Deep-MVLM (Multi-view Consensus CNN for 3D Facial Landmark Placement) framework'ü kullanarak 3D yüz landmarkları tahmini yapar.

## Proje Detayları

**Deep-MVLM** 3D yüz taramalarında landmark yerleştirmek için çok-görünüm konsensüs CNN yaklaşımı kullanır:

- **73 landmark** DTU3D landmark setini destekler
- **Çoklu rendering türleri**: RGB, geometry, depth, RGB+depth, geometry+depth
- **Çoklu format desteği**: OBJ, WRL, VTK, STL, PLY
- **Otomatik hizalama** ve pre-processing yetenekleri

## Gerçekleştirilen Testler

### 1. testmeshA.obj Tahmini (RGB Rendering)
- **Konfigürasyon**: `DTU3D-RGB.json`
- **Sonuç**: Çok başarılı ✅
- **RANSAC Error**: 1.57 (çok düşük)
- **Landmark sayısı**: 73
- **Rendering süresi**: 0.69 saniye
- **Model tahmini süresi**: 52.61 saniye

### 2. PLY Dosyası Tahminleri (Geometry Rendering)

#### assets/files/class1/men/1.ply
- **Konfigürasyon**: `DTU3D-PLY-geometry.json`
- **RANSAC Error**: 10,958,914 (yüksek)
- **Landmark sayısı**: 73
- **Hizalama**: Merkezi hizalama + scale=0.1

#### assets/files/class1/men/2.ply  
- **Konfigürasyon**: `DTU3D-PLY-geometry.json`
- **RANSAC Error**: 9,589,051 (yüksek ama 1.ply'den daha iyi)
- **Landmark sayısı**: 73
- **Hizalama**: Merkezi hizalama + scale=0.1

## Karşılaştırma Analizi

### OBJ vs PLY Landmark Farkları:
- **testmeshA.obj vs 1.ply**: Ortalama 114.17 birim fark
- **testmeshA.obj vs 2.ply**: Ortalama 116.35 birim fark  
- **1.ply vs 2.ply**: Ortalama 85.54 birim fark

### Koordinat Aralıkları:
```
testmeshA.obj (RGB):
  X: -69.57 to 76.64
  Y: -82.59 to 47.40  
  Z: -3.96 to 120.55
  Merkez: (5.90, -7.20, 83.05)

1.ply (Geometry):
  X: -107.60 to 106.82
  Y: -107.65 to 110.46
  Z: 1.65 to 138.18
  Merkez: (51.70, -3.11, 59.07)

2.ply (Geometry):
  X: -107.18 to 107.82
  Y: -112.78 to 121.17
  Z: -0.05 to 158.92
  Merkez: (44.44, -31.70, 54.37)
```

## PLY Dosyaları İçin Optimal Konfigürasyon

PLY dosyaları için oluşturulan özelleştirilmiş config (`DTU3D-PLY-optimized.json`):

### Ana Özellikler:
- **Rendering**: `geometry+depth` (hem geometri hem depth bilgisi)
- **Hizalama**: Merkezi kütle hizalaması aktif
- **Scale**: 0.01 (çok küçük ölçekleme)
- **Pre-aligned dosya yazma**: Aktif

### Hizalama Parametreleri:
```json
"pre-align": {
    "align_center_of_mass": true,
    "rot_x": 0,
    "rot_y": 0, 
    "rot_z": 0,
    "scale": 0.01,
    "write_pre_aligned": true
}
```

## Sonuçlar ve Öneriler

### ✅ Başarılı Aspectler:
1. **OBJ dosyası** RGB rendering ile mükemmel sonuç
2. **PLY dosyaları** işlenebiliyor ve landmark üretiliyor
3. **73 landmark** her durumda başarıyla üretiliyor

### ⚠️ İyileştirme Gereken Alanlar:
1. **PLY hizalama** - RANSAC error'ları çok yüksek
2. **Scale faktörü** - PLY dosyaları için daha iyi ölçekleme gerekli
3. **Rotation parametreleri** - PLY yönelimi için optimizasyon

### 🔧 PLY Hizalama Stratejisi:
1. **Merkezi kütle hizalaması** kullan
2. **Scale faktörünü** 0.001-0.1 arasında test et
3. **Rotasyon açılarını** PLY dosya formatına göre ayarla
4. **geometry+depth** rendering tercih et
5. **Pre-aligned dosyalar** yazarak hizalamayı kontrol et

Bu analiz, Deep-MVLM'nin OBJ dosyalarında çok başarılı olduğunu, PLY dosyalarında ise hizalama optimizasyonu gerektiğini göstermektedir.
