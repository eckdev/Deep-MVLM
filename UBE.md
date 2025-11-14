# 🧠 Deep-MVLM PLY Processing Guide

## 🚀 **Ana Kullanım Komutları:**

### 🎯 **Tek PLY Dosyası İşleme:**
```bash
# Anatomical Alignment (Birincil Yöntem)
python anatomical_ply_preprocessor.py input.ply output.ply
python predict.py --c configs/DTU3D-anatomical.json --n output.ply

# Ultimate Preprocessing (Alternatif Yöntem)
python ultimate_ply_preprocessor.py input.ply aligned.ply
python predict.py --c configs/DTU3D-PLY-ultimate-final.json --n aligned.ply

# Scale-Free Alignment (Manuel Landmark Compatible)
python scale_free_aligner.py input.ply scale_free.ply
python predict.py --c configs/DTU3D-scale-free.json --n scale_free.ply

# Ultimate Scale-Free Alignment (Ultimate + Manuel Landmark Compatible)  
python ultimate_scale_free_preprocessor.py input.ply ultimate_aligned.ply
python predict.py --c configs/DTU3D-scale-free.json --n ultimate_aligned.ply

# Hybrid Scale-Free Alignment (Auto-Select Best Method + Manuel Landmark Compatible)
python hybrid_scale_free_aligner.py input.ply hybrid_aligned.ply
python predict.py --c configs/DTU3D-hybrid-anatomical.json --n hybrid_aligned.ply
```

### 📊 **Batch Processing:**
```bash
# Toplu anatomical processing (Önerilen)
python batch_anatomical_processor.py

# Comprehensive test suite (Tüm PLY dosyaları)
python eyuptest.py
```

### 🔧 **Hybrid Approach:**
```bash
# Hybrid processing (Her iki yöntemi test et)
python hybrid_ply_processor.py input.ply

# Specialized processing
python hybrid_ply_processor.py input.ply anatomical    # Sadece anatomical
python hybrid_ply_processor.py input.ply ultimate      # Sadece ultimate
```

## � **Aktif Araçlar:**

### 🔧 **Core Processing:**
- **`anatomical_aligner.py`** - Ana alignment sistemi
- **`scale_free_aligner.py`** - Manuel landmark compatible alignment  
- **`texture_preserving_scale_free_aligner.py`** - Texture + Landmark preserving
- **`ultimate_scale_free_preprocessor.py`** - Ultimate + Scale-free preprocessing
- **`hybrid_scale_free_aligner.py`** - Auto-select best method + Scale-free
- **`batch_anatomical_processor.py`** - Toplu işleme
- **`ultimate_ply_preprocessor.py`** - Alternatif preprocessing
- **`eyuptest.py`** - Kapsamlı test suite

### 📊 **Analysis Tools:**
- **`comprehensive_ply_analyzer.py`** - Detaylı analiz
- **`poor_performance_analyzer.py`** - Performans analizi
- **`targeted_ply_fixer.py`** - Hedefli düzeltmeler
- **`hybrid_ply_processor.py`** - Hybrid processing
- **`landmark_coordinate_transformer.py`** - Manuel landmark transform

## 🎯 **Performans Sonuçları:**

### ✅ **Başarı Metrikleri:**
- **Anatomical Alignment**: %59.1 başarı oranı
- **Ultimate Preprocessing**: %80+ optimize başarı
- **Hybrid Approach**: %77.3 genel başarı
- **Best Performance**: 3.79 RANSAC error (anatomical)

### 📈 **Optimal Kullanım:**
1. **İlk tercih**: `anatomical_aligner.py` (Çoğu dosya için ideal)
2. **Backup**: `ultimate_ply_preprocessor.py` (Problem durumlarında)
3. **Test**: `eyuptest.py` (Comprehensive analysis)
4. **Batch**: `batch_anatomical_processor.py` (Toplu işleme)

## 🔄 **Workflow Önerisi:**
```bash
# 1. Batch test ile genel durumu gör
python eyuptest.py

# 2. Anatomical alignment ile başla
python anatomical_aligner.py input.ply output.ply

# 3. Problem varsa ultimate dene
python ultimate_ply_preprocessor.py input.ply aligned.ply

# 4. Hybrid approach ile optimize et
python hybrid_ply_processor.py input.ply
```
