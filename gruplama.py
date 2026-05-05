import pandas as pd
import numpy as np
import math

# Veriyi oku
df = pd.read_csv('data.csv')

# NaN'ları boş string ile değiştir (Eğer boş alan varsa)
df = df.fillna('')

# Sütun adlarını belirle (Dosyadaki isimleri dinamik almak için)
cols = df.columns
col_name = cols[0]
col_recommended = cols[1]
col_choice1 = cols[2]
col_choice2 = cols[3]
col_choice3 = cols[4]
col_audiences = cols[5]

# --- 1. BENZERLİK FONKSİYONU ---
def calculate_similarity(row1, row2):
    score = 0
    
    # 1. ÖNCELİK: Önerilen Konu ve Hedef Kitle (En yüksek ağırlık)
    # Önerilen konu eşleşmesi
    if row1[col_recommended] == row2[col_recommended] and row1[col_recommended] != '':
        score += 20
        
    # Hedef Kitleler eşleşmesi (Virgülle ayrılmış değerleri parçalayıp küme olarak kesiştirelim)
    aud1 = set([x.strip() for x in row1[col_audiences].split(',') if x.strip()])
    aud2 = set([x.strip() for x in row2[col_audiences].split(',') if x.strip()])
    common_aud = len(aud1.intersection(aud2))
    score += common_aud * 20 
        
    # SONRAKİ ÖNCELİKLER: 1.Tercih, 2.Tercih, 3.Tercih sıralaması
    if row1[col_choice1] == row2[col_choice1] and row1[col_choice1] != '':
        score += 10 
    if row1[col_choice2] == row2[col_choice2] and row1[col_choice2] != '':
        score += 7
    if row1[col_choice3] == row2[col_choice3] and row1[col_choice3] != '':
        score += 4
        
    # Çapraz eşleşmeler (Ortak alanların sayısına göre bonus puan)
    choices1 = {row1[col_choice1], row1[col_choice2], row1[col_choice3]}
    choices2 = {row2[col_choice1], row2[col_choice2], row2[col_choice3]}
    common_choices = len(choices1.intersection(choices2))
    score += common_choices * 2
    
    return score

n = len(df)
print(f"Toplam okunan kişi sayısı: {n}")

# --- 2. BENZERLİK MATRİSİNİ HESAPLAMA ---
sim_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(i+1, n):
        sim = calculate_similarity(df.iloc[i], df.iloc[j])
        sim_matrix[i, j] = sim
        sim_matrix[j, i] = sim

# --- 3. KISITLI (EŞİT DAĞILIMLI) KÜMELEME ---
num_groups = 21 # Kullanıcı 21 grup oluşturulmasını istedi
MAX_GROUP_SIZE = math.ceil(n / num_groups) # Her grubun alabileceği maksimum kişi sayısı

groups = {i: [] for i in range(num_groups)}
unassigned = set(range(n))

# Gruplara başlangıç noktaları atayalım (İlk kişileri sırayla atıyoruz)
seed_indices = list(unassigned)[:num_groups]
for i, seed in enumerate(seed_indices):
    groups[i].append(seed)
    unassigned.remove(seed)

# Kalan kişileri "en çok benzedikleri" gruba atama işlemi
while unassigned:
    # Her döngüde atanmayan bir kişiyi alalım
    person = list(unassigned)[0]
    
    best_group = -1
    best_sim = -1
    
    for g_idx, members in groups.items():
        if len(members) >= MAX_GROUP_SIZE:
            continue # Grup dolduysa atla
            
        # Kişinin gruptaki diğer kişilerle ortalama benzerliğini bulalım
        if len(members) == 0:
            avg_sim = 0
        else:
            avg_sim = np.mean([sim_matrix[person, m] for m in members])
            
        if avg_sim > best_sim:
            best_sim = avg_sim
            best_group = g_idx
            
    if best_group != -1:
        groups[best_group].append(person)
        unassigned.remove(person)
    else:
        # Eğer olası boş bir grup kalmadıysa (bütün gruplar maksimum kapasiteyse ki bu normalde n > kapasite * num_groups olduğunda olur)
        # En az üyesi olan gruba ekle
        min_group = min(groups.keys(), key=lambda k: len(groups[k]))
        groups[min_group].append(person)
        unassigned.remove(person)

# --- 4. TAKAS OPTİMİZASYONU (SWAP) VE KALİTE SKORU ---
def get_person_group_sim(person, group_members, sim_mat):
    if len(group_members) == 0: return 0
    return sum(sim_mat[person, m] for m in group_members if m != person)

def calculate_quality_score(groups_dict, sim_mat):
    total_score = 0
    total_pairs = 0
    for g_idx, members in groups_dict.items():
        for i in range(len(members)):
            for j in range(i+1, len(members)):
                total_score += sim_mat[members[i], members[j]]
                total_pairs += 1
    return total_score / total_pairs if total_pairs > 0 else 0

initial_score = calculate_quality_score(groups, sim_matrix)
print(f"Optimizasyon Öncesi Genel Uyum Skoru (Ortalama Benzerlik): {initial_score:.2f}")

print("Takas (Swap) optimizasyonu başlatılıyor. Bu işlem birkaç saniye sürebilir...")
improvement = True
max_iterations = 20
iteration = 0

while improvement and iteration < max_iterations:
    improvement = False
    iteration += 1
    group_keys = list(groups.keys())
    
    for g1_idx in group_keys:
        for g2_idx in group_keys:
            if g1_idx >= g2_idx: continue
            
            for m1 in list(groups[g1_idx]):
                swap_done = False
                for m2 in list(groups[g2_idx]):
                    
                    g1_others = [x for x in groups[g1_idx] if x != m1]
                    g2_others = [x for x in groups[g2_idx] if x != m2]
                    
                    current_sim = get_person_group_sim(m1, g1_others, sim_matrix) + \
                                  get_person_group_sim(m2, g2_others, sim_matrix)
                                  
                    new_sim = get_person_group_sim(m1, g2_others, sim_matrix) + \
                              get_person_group_sim(m2, g1_others, sim_matrix)
                              
                    if new_sim > current_sim:
                        # Takas yap
                        groups[g1_idx].remove(m1)
                        groups[g1_idx].append(m2)
                        groups[g2_idx].remove(m2)
                        groups[g2_idx].append(m1)
                        improvement = True
                        swap_done = True
                        break 
                if swap_done:
                    pass

final_score = calculate_quality_score(groups, sim_matrix)
print(f"Optimizasyon Sonrası Genel Uyum Skoru: {final_score:.2f} (Döngü sayısı: {iteration})")

# --- 5. SONUÇLARI KAYDETME ---
results = []
for g_idx, members in groups.items():
    for m in members:
        row_data = df.iloc[m].to_dict()
        row_data['Grup No'] = f"Grup {g_idx + 1}"
        results.append(row_data)

# Form doldurmayanları rastgele dağıt
try:
    import random
    df_empty = pd.read_csv('form doldurmayanlar .csv')
    empty_names = df_empty.iloc[:, 0].tolist() # İlk sütun isimler
    
    random.seed(42) # Aynı rastgele dağılımı korumak için
    random.shuffle(empty_names)
    
    group_indices = list(range(21))
    for i, name in enumerate(empty_names):
        g_idx = group_indices[i % 21]
        
        row_data = {col: 'Form Doldurmadı - Rastgele Atandı' for col in df.columns}
        row_data[df.columns[0]] = name
        row_data['Grup No'] = f"Grup {g_idx + 1}"
        
        results.append(row_data)
        groups[g_idx].append(-1) # Gerçek kişi olmadığını belirtmek için -1 ekliyoruz
except Exception as e:
    print(f"\nForm doldurmayanlar dosyası işlenirken hata oluştu (Dosya bulunamamış olabilir): {e}")

result_df = pd.DataFrame(results)

# Kolon sıralamasını düzenle
cols_order = ['Grup No'] + list(df.columns)
result_df = result_df[cols_order]

# Excel ve CSV olarak kaydet
result_df.to_csv('gruplanmis_kisiler.csv', index=False, encoding='utf-8-sig')
print("\nVeriler 'gruplanmis_kisiler.csv' dosyasına kaydedildi.")

# EXCEL DOSYASI OLUŞTURMA (Her grup ayrı sayfa)
try:
    # xlsxwriter motorunu kullanarak Excel writer objesi oluştur
    excel_path = 'dashboard/public/YetGen_Gruplar.xlsx'
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    workbook = writer.book
    
    # Başlık stili
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#2563eb',
        'font_color': 'white',
        'border': 1
    })
    
    # Her Grup için Ayrı Sayfa (Sheet) oluştur
    for g in sorted(groups.keys()):
        group_name = f"Grup {g + 1}"
        group_data = result_df[result_df['Grup No'] == group_name]
        
        group_data.to_excel(writer, sheet_name=group_name, index=False)
        worksheet = writer.sheets[group_name]
        
        for col_num, value in enumerate(group_data.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 25)
    
    # Analiz ve Algoritma Bilgisi Sayfası
    worksheet_info = workbook.add_worksheet('Algoritma Raporu')
    
    title_format = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#2C4D75'})
    subtitle_format = workbook.add_format({'bold': True, 'font_size': 12, 'font_color': '#4F81BD'})
    text_format = workbook.add_format({'font_size': 11, 'text_wrap': True})
    
    worksheet_info.set_column('A:A', 25)
    worksheet_info.set_column('B:B', 20)
    worksheet_info.set_column('C:C', 100)
    
    worksheet_info.write('A1', 'YetGen Kümeleme Algoritması Raporu', title_format)
    worksheet_info.write('A3', '1. Algoritma ve Puanlama Mantığı:', subtitle_format)
    
    algoritma_metni = (
        "Algoritma, katılımcıları form tercihlerine göre birbirleriyle eşleştirir. "
        "En yüksek ağırlık (20 puan) 'Önerilen Konu' ve ortak 'Hedef Kitle'lere verilmiştir. "
        "Daha sonra 1. Tercih (10p), 2. Tercih (7p) ve 3. Tercih (4p) dikkate alınarak kişilerin "
        "birbirlerine olan 'Uyum Skoru' hesaplanır. Her kişi, kendine en çok benzeyen kişilerin olduğu gruba atanır. "
        "Son olarak takas (swap) işlemi yapılarak grupların genel uyumu maksimuma çıkarılır."
    )
    worksheet_info.merge_range('A4:C7', algoritma_metni, text_format)
    
    worksheet_info.write('A9', '2. Grup Uyum Skorları ve Detaylar:', subtitle_format)
    
    # Tablo başlıkları
    table_header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
    worksheet_info.write('A10', 'Grup Adı', table_header_format)
    worksheet_info.write('B10', 'Kişi Sayısı', table_header_format)
    worksheet_info.write('C10', 'Ortalama Uyum Skoru ve Açıklama', table_header_format)
    
    row_idx = 10
    print("\n--- GRUP BİLGİLERİ ---")
    for g in sorted(groups.keys()):
        g_members = groups[g]
        real_members = [m for m in g_members if m != -1] # Sadece formu dolduranları al
        
        if len(real_members) > 1:
            g_sim = sum(sim_matrix[real_members[i], real_members[j]] for i in range(len(real_members)) for j in range(i+1, len(real_members)))
            g_pairs = (len(real_members) * (len(real_members) - 1)) / 2
            avg_g_sim = g_sim / g_pairs
        else:
            avg_g_sim = 0
            
        print(f"Grup {g+1} içerisindeki kişi sayısı: {len(g_members)} (Form Dolduran: {len(real_members)}, Grup Uyum Skoru: {avg_g_sim:.2f})")
        
        # Skora göre yorum
        if avg_g_sim >= 60:
            yorum = "Çok Yüksek Uyum (Grup üyelerinin hedefleri ve konuları neredeyse birebir örtüşüyor)"
            color = '#C6EFCE' # Yeşil
            font_color = '#006100'
        elif avg_g_sim >= 40:
            yorum = "Yüksek Uyum (Grup üyelerinin büyük bölümü ortak konularda buluşmuş)"
            color = '#FFEB9C' # Sarı
            font_color = '#9C5700'
        else:
            yorum = "Normal Uyum (Ortak tercihleri var, ancak konular biraz daha çeşitlilik gösteriyor)"
            color = '#FFC7CE' # Kırmızı
            font_color = '#9C0006'
            
        cell_format = workbook.add_format({'border': 1, 'bg_color': color, 'font_color': font_color})
        default_format = workbook.add_format({'border': 1, 'align': 'center'})
        
        worksheet_info.write(row_idx, 0, f"Grup {g+1}", default_format)
        worksheet_info.write(row_idx, 1, f"Toplam: {len(g_members)} (Rastgele Atanan: {len(g_members) - len(real_members)})", default_format)
        worksheet_info.write(row_idx, 2, f"Skor: {avg_g_sim:.2f}  |  {yorum}", cell_format)
        row_idx += 1

    writer.close()
    print(f"\nProfesyonel raporlu Excel dosyası '{excel_path}' adıyla kaydedildi.")
    
    # Eski lokasyona da kopyasını bırakalım ki kullanıcı ana dizinde de görsün
    import shutil
    shutil.copy(excel_path, 'gruplanmis_kisiler_raporlu.xlsx')
    
except Exception as e:
    print(f"Excel oluşturulurken hata oluştu: {e}")
