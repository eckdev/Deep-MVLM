#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean

def load_landmarks(filename):
    """Load landmarks from text file"""
    landmarks = []
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 3:
                x, y, z = map(float, parts)
                landmarks.append([x, y, z])
    return np.array(landmarks)

def analyze_landmarks(landmarks1, landmarks2, name1, name2):
    """Analyze and compare two sets of landmarks"""
    print(f"\n=== Landmark Analizi: {name1} vs {name2} ===")
    
    # Basic statistics
    print(f"\n{name1} İstatistikleri:")
    print(f"  Landmark sayısı: {len(landmarks1)}")
    print(f"  X koordinat aralığı: {landmarks1[:, 0].min():.2f} - {landmarks1[:, 0].max():.2f}")
    print(f"  Y koordinat aralığı: {landmarks1[:, 1].min():.2f} - {landmarks1[:, 1].max():.2f}")
    print(f"  Z koordinat aralığı: {landmarks1[:, 2].min():.2f} - {landmarks1[:, 2].max():.2f}")
    print(f"  Merkez: ({landmarks1.mean(axis=0)[0]:.2f}, {landmarks1.mean(axis=0)[1]:.2f}, {landmarks1.mean(axis=0)[2]:.2f})")
    
    print(f"\n{name2} İstatistikleri:")
    print(f"  Landmark sayısı: {len(landmarks2)}")
    print(f"  X koordinat aralığı: {landmarks2[:, 0].min():.2f} - {landmarks2[:, 0].max():.2f}")
    print(f"  Y koordinat aralığı: {landmarks2[:, 1].min():.2f} - {landmarks2[:, 1].max():.2f}")
    print(f"  Z koordinat aralığı: {landmarks2[:, 2].min():.2f} - {landmarks2[:, 2].max():.2f}")
    print(f"  Merkez: ({landmarks2.mean(axis=0)[0]:.2f}, {landmarks2.mean(axis=0)[1]:.2f}, {landmarks2.mean(axis=0)[2]:.2f})")
    
    # Distance analysis (only if same number of landmarks)
    if len(landmarks1) == len(landmarks2):
        distances = []
        for i in range(len(landmarks1)):
            dist = euclidean(landmarks1[i], landmarks2[i])
            distances.append(dist)
        
        distances = np.array(distances)
        print(f"\nNokta-nokta mesafe analizi:")
        print(f"  Ortalama mesafe: {distances.mean():.2f}")
        print(f"  Medyan mesafe: {np.median(distances):.2f}")
        print(f"  Min mesafe: {distances.min():.2f}")
        print(f"  Max mesafe: {distances.max():.2f}")
        print(f"  Standart sapma: {distances.std():.2f}")
        
        # Find most different landmarks
        max_dist_idx = np.argmax(distances)
        print(f"  En farklı landmark #{max_dist_idx}: {distances[max_dist_idx]:.2f} birim")
        
        return distances
    else:
        print("\nLandmark sayıları farklı - nokta-nokta karşılaştırma yapılamıyor")
        return None

def main():
    # Load all landmark files
    testmesh_landmarks = load_landmarks('assets/testmeshA_landmarks.txt')
    ply1_landmarks = load_landmarks('assets/files/class1/men/1_landmarks.txt')
    ply2_landmarks = load_landmarks('assets/files/class1/men/2_landmarks.txt')
    
    print("=== DEEP-MVLM TAHMIN KARŞILAŞTIRMASI ===")
    
    # Compare testmeshA.obj vs 1.ply
    distances1 = analyze_landmarks(testmesh_landmarks, ply1_landmarks, 
                                 "testmeshA.obj (RGB)", "1.ply (Geometry)")
    
    # Compare testmeshA.obj vs 2.ply  
    distances2 = analyze_landmarks(testmesh_landmarks, ply2_landmarks,
                                 "testmeshA.obj (RGB)", "2.ply (Geometry)")
    
    # Compare 1.ply vs 2.ply
    distances3 = analyze_landmarks(ply1_landmarks, ply2_landmarks,
                                 "1.ply (Geometry)", "2.ply (Geometry)")
    
    print("\n=== KARŞILAŞTIRMA ÖZETİ ===")
    print(f"testmeshA.obj, RGB rendering ile çok başarılı tahmin yapıldı (RANSAC error: 1.57)")
    print(f"1.ply, Geometry rendering ile orta başarılı tahmin (RANSAC error: 10958914)")  
    print(f"2.ply, Geometry rendering ile orta başarılı tahmin (RANSAC error: 9589051)")
    print(f"\nPLY dosyaları için daha iyi hizalama gerekiyor.")
    
    if distances1 is not None:
        print(f"\nOBJ vs PLY1 ortalama fark: {distances1.mean():.2f} birim")
    if distances2 is not None:
        print(f"OBJ vs PLY2 ortalama fark: {distances2.mean():.2f} birim")
    if distances3 is not None:
        print(f"PLY1 vs PLY2 ortalama fark: {distances3.mean():.2f} birim")

if __name__ == "__main__":
    main()
