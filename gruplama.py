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

# Tercih odaklı konu puanlaması (yüksek ağırlık)
TOPIC_PREFERENCE_WEIGHTS = {
    'choice1': 90,
    'choice2': 60,
    'choice3': 40,
    'recommended': 35
}
DUPLICATE_TOPIC_BONUS = 30
AUDIENCE_MATCH_SCORE = 1  # Hedef kitle etkisi minimum
TOPIC_MISMATCH_PENALTY = -35

def parse_choices(row):
    return [row[col_choice1], row[col_choice2], row[col_choice3]]

def get_topic_preference_score(row, topic):
    score = 0
    choices = parse_choices(row)

    if choices[0] == topic and topic != '':
        score += TOPIC_PREFERENCE_WEIGHTS['choice1']
    if choices[1] == topic and topic != '':
        score += TOPIC_PREFERENCE_WEIGHTS['choice2']
    if choices[2] == topic and topic != '':
        score += TOPIC_PREFERENCE_WEIGHTS['choice3']
    if row[col_recommended] == topic and topic != '':
        score += TOPIC_PREFERENCE_WEIGHTS['recommended']

    # Aynı konuyu birden fazla tercihte tekrar eden katılımcıları güçlendir
    repeat_count = sum(1 for c in choices if c == topic and c != '')
    if repeat_count >= 2:
        score += (repeat_count - 1) * DUPLICATE_TOPIC_BONUS
    return score

# --- 1. BENZERLİK FONKSİYONU ---
def calculate_similarity(row1, row2):
    score = 0

    # Önerilen konu eşleşmesi
    if row1[col_recommended] == row2[col_recommended] and row1[col_recommended] != '':
        score += 30

    # Tercih konuları (sıralı, yüksek ağırlık)
    if row1[col_choice1] == row2[col_choice1] and row1[col_choice1] != '':
        score += 40
    if row1[col_choice2] == row2[col_choice2] and row1[col_choice2] != '':
        score += 24
    if row1[col_choice3] == row2[col_choice3] and row1[col_choice3] != '':
        score += 12

    # Çapraz tercih eşleşmeleri (boş değerler hariç)
    choices1 = {c for c in parse_choices(row1) if c}
    choices2 = {c for c in parse_choices(row2) if c}
    common_choices = len(choices1.intersection(choices2))
    score += common_choices * 8

    # Hedef Kitleler eşleşmesi (minimum etki)
    aud1 = set([x.strip() for x in row1[col_audiences].split(',') if x.strip()])
    aud2 = set([x.strip() for x in row2[col_audiences].split(',') if x.strip()])
    common_aud = len(aud1.intersection(aud2))
    score += common_aud * AUDIENCE_MATCH_SCORE

    return score

n = len(df)
print(f"Toplam okunan kişi sayısı: {n}")

# Form doldurmayanları erken oku: hedef kapasiteyi toplam kişiye göre kuracağız
try:
    df_empty = pd.read_csv('form doldurmayanlar .csv')
    empty_names = df_empty.iloc[:, 0].dropna().astype(str).tolist()
except Exception:
    df_empty = None
    empty_names = []

empty_count = len(empty_names)
total_participants = n + empty_count
print(f"Form doldurmayan kişi sayısı: {empty_count}")
print(f"Toplam kişi sayısı (genel): {total_participants}")

# --- 2. BENZERLİK MATRİSİNİ HESAPLAMA ---
sim_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(i+1, n):
        sim = calculate_similarity(df.iloc[i], df.iloc[j])
        sim_matrix[i, j] = sim
        sim_matrix[j, i] = sim

# --- 3. KISITLI (EŞİT DAĞILIMLI) KÜMELEME ---
num_groups = 21  # 7 konu x 3 grup

def build_balanced_targets(total_count, group_count):
    base = total_count // group_count
    remainder = total_count % group_count
    return [base + (1 if i < remainder else 0) for i in range(group_count)]

# Faz 1: yalnızca form dolduranlar eşit dağılsın (255 => 12/13 gibi)
form_targets = build_balanced_targets(n, num_groups)
# Faz 2: tüm katılımcılar eşit dağılsın (form + form doldurmayan)
total_targets = build_balanced_targets(total_participants, num_groups)

group_profiles = {
    0: {'topic': 'Eşit ve Özgür Toplum', 'audience': 'Gençler'},
    1: {'topic': 'Eşit ve Özgür Toplum', 'audience': 'Kadınlar'},
    2: {'topic': 'Eşit ve Özgür Toplum', 'audience': 'İstanbullular'},
    3: {'topic': 'Etkin ve Kapsayıcı Hareketlilik', 'audience': 'İstanbullular'},
    4: {'topic': 'Etkin ve Kapsayıcı Hareketlilik', 'audience': 'Gençler'},
    5: {'topic': 'Etkin ve Kapsayıcı Hareketlilik', 'audience': 'Düşük gelirli gruplar'},
    6: {'topic': 'Çevreyi Koruyan ve İklime Uyum Sağlayan Kent', 'audience': 'İstanbullular'},
    7: {'topic': 'Çevreyi Koruyan ve İklime Uyum Sağlayan Kent', 'audience': 'Gençler'},
    8: {'topic': 'Çevreyi Koruyan ve İklime Uyum Sağlayan Kent', 'audience': 'Kadınlar'},
    9: {'topic': 'Herkes İçin Erişilebilir ve Adil Kentsel Olanaklar', 'audience': 'Gençler'},
    10: {'topic': 'Herkes İçin Erişilebilir ve Adil Kentsel Olanaklar', 'audience': 'İstanbullular'},
    11: {'topic': 'Herkes İçin Erişilebilir ve Adil Kentsel Olanaklar', 'audience': 'Kadınlar'},
    12: {'topic': 'İyi Yaşam Sağlayan Canlı ve Duyarlı Mekanlar', 'audience': 'Kadınlar'},
    13: {'topic': 'İyi Yaşam Sağlayan Canlı ve Duyarlı Mekanlar', 'audience': 'Gençler'},
    14: {'topic': 'İyi Yaşam Sağlayan Canlı ve Duyarlı Mekanlar', 'audience': 'İstanbullular'},
    15: {'topic': 'Dönüştüren ve Dayanıklı Ekonomi', 'audience': 'Gençler'},
    16: {'topic': 'Dönüştüren ve Dayanıklı Ekonomi', 'audience': 'İstanbullular'},
    17: {'topic': 'Dönüştüren ve Dayanıklı Ekonomi', 'audience': 'Düşük gelirli gruplar'},
    18: {'topic': 'Bütünleşik ve Akıllı Altyapı Sistemleri', 'audience': 'Gençler'},
    19: {'topic': 'Bütünleşik ve Akıllı Altyapı Sistemleri', 'audience': 'İstanbullular'},
    20: {'topic': 'Bütünleşik ve Akıllı Altyapı Sistemleri', 'audience': 'Düşük gelirli gruplar'}
}

groups = {i: [] for i in range(num_groups)}
unassigned = set(range(n))

# Gruplara başlangıç noktaları atayalım (Profile en uygun kişiyi bulalım)
for i in range(num_groups):
    best_seed = -1
    best_score = -1
    profile = group_profiles[i]
    
    for candidate in unassigned:
        row = df.iloc[candidate]
        score = get_topic_preference_score(row, profile['topic'])
        if profile['audience'] in row[col_audiences]:
            score += AUDIENCE_MATCH_SCORE

        if score > best_score:
            best_score = score
            best_seed = candidate
            
    if best_seed != -1:
        groups[i].append(best_seed)
        unassigned.remove(best_seed)
    else:
        # Uygun bulunamazsa rastgele birini ata
        seed = list(unassigned)[0]
        groups[i].append(seed)
        unassigned.remove(seed)

# Kalan kişileri "en çok benzedikleri" gruba atama işlemi
while unassigned:
    # Her döngüde atanmayan bir kişiyi alalım
    person = list(unassigned)[0]
    
    best_group = -1
    best_sim = -1
    
    for g_idx, members in groups.items():
        if len(members) >= form_targets[g_idx]:
            continue # Grup dolduysa atla
            
        # Kişinin gruptaki diğer kişilerle ortalama benzerliğini bulalım
        if len(members) == 0:
            avg_sim = 0
        else:
            avg_sim = np.mean([sim_matrix[person, m] for m in members])
            
        # Grupta tanımlı profile uygunluk bonusu (tercih bazlı güçlü eşleştirme)
        profile = group_profiles[g_idx]
        person_row = df.iloc[person]
        topic_score = get_topic_preference_score(person_row, profile['topic'])
        avg_sim += topic_score

        if topic_score == 0:
            # Kişi bu konuya hiç ilgi belirtmediyse güçlü ceza uygula
            avg_sim += TOPIC_MISMATCH_PENALTY

        if profile['audience'] in person_row[col_audiences]:
            avg_sim += AUDIENCE_MATCH_SCORE
            
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

def get_assignment_score(person, group_idx, groups_dict, sim_mat):
    members = groups_dict[group_idx]
    if len(members) == 0:
        avg_sim = 0
    else:
        avg_sim = np.mean([sim_mat[person, m] for m in members if m != person]) if any(m != person for m in members) else 0

    row = df.iloc[person]
    profile = group_profiles[group_idx]
    topic_score = get_topic_preference_score(row, profile['topic'])
    audience_score = AUDIENCE_MATCH_SCORE if profile['audience'] in row[col_audiences] else 0
    mismatch_penalty = TOPIC_MISMATCH_PENALTY if topic_score == 0 else 0
    return avg_sim + topic_score + audience_score + mismatch_penalty

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
                    
                    # Swap kararını sadece benzerlik değil, tercih-profil uyumuna göre de ver
                    temp_groups = {k: list(v) for k, v in groups.items()}
                    temp_groups[g1_idx] = list(g1_others) + [m1]
                    temp_groups[g2_idx] = list(g2_others) + [m2]
                    current_sim = get_assignment_score(m1, g1_idx, temp_groups, sim_matrix) + \
                                  get_assignment_score(m2, g2_idx, temp_groups, sim_matrix)

                    temp_groups[g1_idx] = list(g1_others) + [m2]
                    temp_groups[g2_idx] = list(g2_others) + [m1]
                    new_sim = get_assignment_score(m1, g2_idx, temp_groups, sim_matrix) + \
                              get_assignment_score(m2, g1_idx, temp_groups, sim_matrix)
                              
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
    profile = group_profiles[g_idx]
    for m in members:
        row_data = df.iloc[m].to_dict()
        row_data['Grup No'] = f"Grup {g_idx + 1}"
        row_data['Atanan Konu'] = profile['topic']
        row_data['Atanan Hedef Kitle'] = profile['audience']
        results.append(row_data)

# Form doldurmayanları homojen şekilde dağıt (kalan kotaya göre)
try:
    import random
    random.seed(42)
    random.shuffle(empty_names)

    def group_cohesion_score(g_idx):
        """Form dolduran üyelerin grup içi ortalama benzerlik skoru."""
        real_members = [m for m in groups[g_idx] if m != -1]
        if len(real_members) <= 1:
            return 0
        g_sim = sum(
            sim_matrix[real_members[i], real_members[j]]
            for i in range(len(real_members))
            for j in range(i + 1, len(real_members))
        )
        g_pairs = (len(real_members) * (len(real_members) - 1)) / 2
        return g_sim / g_pairs if g_pairs > 0 else 0

    for name in empty_names:
        available_groups = [g for g in range(num_groups) if len(groups[g]) < total_targets[g]]
        if not available_groups:
            # Güvenlik: hedefler doluysa en az kişili gruba bırak
            g_idx = min(range(num_groups), key=lambda g: len(groups[g]))
        else:
            # Önce homojenlik (kalan kapasite), eşitlikte grup uyum skoru yüksek olana ata
            g_idx = max(available_groups, key=lambda g: (
                total_targets[g] - len(groups[g]),
                group_cohesion_score(g),
                -len(groups[g])
            ))

        row_data = {col: 'Form Doldurmadı - Homojen Atandı' for col in df.columns}
        row_data[df.columns[0]] = name
        row_data['Grup No'] = f"Grup {g_idx + 1}"
        row_data['Atanan Konu'] = group_profiles[g_idx]['topic']
        row_data['Atanan Hedef Kitle'] = group_profiles[g_idx]['audience']

        results.append(row_data)
        groups[g_idx].append(-1)  # Form doldurmayan placeholder
except Exception as e:
    print(f"\nForm doldurmayanlar dağıtılırken hata oluştu: {e}")

result_df = pd.DataFrame(results)

# Kolon sıralamasını düzenle
cols_order = ['Grup No', 'Atanan Konu', 'Atanan Hedef Kitle'] + list(df.columns)
result_df = result_df[cols_order]

# Excel ve CSV olarak kaydet
result_df.to_csv('gruplanmis_kisiler.csv', index=False, encoding='utf-8-sig')
print("\nVeriler 'gruplanmis_kisiler.csv' dosyasına kaydedildi.")

# Dashboard'un okuduğu public data dosyasını da her çalıştırmada güncelle
dashboard_csv_path = 'dashboard/public/data.csv'
result_df.to_csv(dashboard_csv_path, index=False, encoding='utf-8-sig')
print(f"Dashboard verisi '{dashboard_csv_path}' dosyasına güncellendi.")

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
        "Algoritma, oluşturulan 21 gruba baştan 7 proje konusunun her birinden 3'er tane olacak şekilde sabit profiller (Konu ve Hedef Kitle) atar. "
        "Katılımcılar gruplara dağıtılırken tercih konuları ana belirleyicidir: 1. tercih (+90), 2. tercih (+60), 3. tercih (+40), önerilen konu (+35) "
        "ve aynı konuyu birden çok tercihte tekrar etme bonusu uygulanır. Bu sayede konu tercihi güçlü şekilde korunur. "
        "Hedef kitle eşleşmesi bilinçli olarak minimum etkide tutulur (+1). "
        "Kapasite kısıtlamaları dâhilinde, herkesin en uygun gruba düşmesi ve genel uyumun en yüksek seviyede tutulması sağlanır."
    )
    worksheet_info.merge_range('A4:D7', algoritma_metni, text_format)
    
    worksheet_info.write('A9', '2. Grup Özellikleri ve Detaylar:', subtitle_format)
    
    # Tablo başlıkları
    table_header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
    worksheet_info.write('A10', 'Grup Adı', table_header_format)
    worksheet_info.write('B10', 'Kişi Sayısı', table_header_format)
    worksheet_info.write('C10', 'Atanan Konu', table_header_format)
    worksheet_info.write('D10', 'Atanan Hedef Kitle', table_header_format)
    
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
        
        # Skora göre yorum (Artık sadece Konu ve Kitleyi de basacağız)
        cell_format = workbook.add_format({'border': 1, 'bg_color': '#f8fafc', 'font_color': '#334155'})
        default_format = workbook.add_format({'border': 1, 'align': 'center'})
        
        worksheet_info.write(row_idx, 0, f"Grup {g+1}", default_format)
        worksheet_info.write(row_idx, 1, f"{len(g_members)} Kişi", default_format)
        worksheet_info.write(row_idx, 2, group_profiles[g]['topic'], cell_format)
        worksheet_info.write(row_idx, 3, group_profiles[g]['audience'], cell_format)
        row_idx += 1

    writer.close()
    print(f"\nProfesyonel raporlu Excel dosyası '{excel_path}' adıyla kaydedildi.")
    
    # Eski lokasyona da kopyasını bırakalım ki kullanıcı ana dizinde de görsün
    import shutil
    shutil.copy(excel_path, 'gruplanmis_kisiler_raporlu.xlsx')
    
except Exception as e:
    print(f"Excel oluşturulurken hata oluştu: {e}")
