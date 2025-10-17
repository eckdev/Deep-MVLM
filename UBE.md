### 🚀 **Kullanım için gereken tek komut:**

```bash
# PLY dosyasını işlemek için #ESKİ:
python ultimate_ply_preprocessor.py input.ply aligned.ply
python predict.py --c configs/DTU3D-PLY-ultimate-final.json --n aligned.ply

# PLY dosyasını işlemek için #YENİ:
python anatomical_ply_preprocessor input.ply anatomical_aligned_[file].ply
python predict.py --c configs/DTU3D-anatomical.json --n anatomical_aligned_[file].ply
```

### 📋 **Test için:**
```bash
python ply_test_suite.py

```