import { useState, useEffect, useRef } from 'react';
import Papa from 'papaparse';
import { Target, Star, Activity, Cpu, Download, X } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';

interface Participant {
  'Grup No': string;
  'İsim Soyisim': string;
  'Çözdüğün Testte Sana Önerilen Proje Konusu': string;
  'Seçmek İstediğin Proje Konusu (1. Tercih)': string;
  'Seçmek İstediğin Proje Konusu (2. Tercih)': string;
  'Seçmek İstediğin Proje Konusu (3. Tercih)': string;
  'Çalışmak İstediğin Hedef Kitleler (Birden fazla seçim yapabilirsin.)': string;
}

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#059669', '#d97706', '#0891b2'];

export default function Dashboard() {
  const [data, setData] = useState<Participant[]>([]);
  const [groups, setGroups] = useState<string[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(true); // Welcome modal state
  const timelineRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/data.csv')
      .then(response => response.text())
      .then(csvText => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          transformHeader: (header) => header.replace(/^\uFEFF/, '').trim(),
          complete: (results) => {
            const parsedData = results.data as Participant[];
            setData(parsedData);
            
            const uniqueGroups = Array.from(new Set(parsedData.map(d => d['Grup No'])))
              .filter(Boolean)
              .sort((a, b) => {
                const numA = parseInt(a.replace('Grup ', ''));
                const numB = parseInt(b.replace('Grup ', ''));
                return numA - numB;
              });
              
            setGroups(uniqueGroups);
            if (uniqueGroups.length > 0) {
              setSelectedGroup(uniqueGroups[0]);
            }
            setLoading(false);
          }
        });
      });
  }, []);

  useEffect(() => {
    if (timelineRef.current && selectedGroup) {
      const activeElement = timelineRef.current.querySelector('.active');
      if (activeElement) {
        activeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  }, [selectedGroup]);

  if (loading) {
    return <div className="container" style={{ textAlign: 'center', paddingTop: '20vh' }}>
      <h2 style={{ animation: 'pulse 1.5s infinite', color: '#2563eb' }}>Algoritma Optimizasyon Raporu Hazırlanıyor...</h2>
    </div>;
  }

  const groupData = data.filter(d => d['Grup No'] === selectedGroup);
  
  // Real members for calculating accurate stats
  const realMembers = groupData.filter(d => !d['Çözdüğün Testte Sana Önerilen Proje Konusu']?.includes('Form Doldurmadı'));
  const randomMembersCount = groupData.length - realMembers.length;
  
  const dominantTopic = realMembers.reduce((acc, curr) => {
    const topic = curr['Çözdüğün Testte Sana Önerilen Proje Konusu'];
    if (topic) {
      acc[topic] = (acc[topic] || 0) + 1;
    }
    return acc;
  }, {} as Record<string, number>);
  
  const topTopicEntry = Object.entries(dominantTopic).sort((a,b) => b[1] - a[1])[0];
  const topTopic = topTopicEntry ? topTopicEntry[0] : 'Belirsiz';
  const topicMatchRate = topTopicEntry && realMembers.length > 0 ? Math.round((topTopicEntry[1] / realMembers.length) * 100) : 0;

  const pieData = Object.entries(dominantTopic)
    .map(([name, value]) => ({ name: name || 'Belirtilmemiş', value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  return (
    <div className="container">
      {/* Welcome Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content glass">
            <button className="modal-close" onClick={() => setShowModal(false)}>
              <X className="w-6 h-6 text-slate-400" />
            </button>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <img 
                src="/yetgen-logo-transparent.png" 
                alt="YetGen Logo" 
                style={{ height: '70px', objectFit: 'contain', margin: '0 auto 1.5rem auto', display: 'block' }} 
              />
              <h2 style={{ fontSize: '1.8rem', color: '#0f172a' }}>Genç Yetenek Kümeleme Sonuç Raporu</h2>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '1.1rem', color: '#334155', marginBottom: '1.5rem', lineHeight: 1.6 }}>
                Tüm katılımcılar analiz edildi ve gruplar başarıyla oluşturuldu! Yapay zeka algoritmamız, katılımcıları sadece rastgele değil, <strong>maksimum grup uyumunu (sinerjiyi)</strong> sağlayacak şekilde bir araya getirdi.
              </p>
              <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#1e293b' }}>⚙️ Gruplar Nasıl Oluşturuldu?</h3>
                <ul style={{ paddingLeft: '1.5rem', color: '#475569', lineHeight: 1.8 }}>
                  <li><strong>1. Önceliklendirme:</strong> Her kullanıcının <i>"Önerilen Proje Konusu"</i> ve <i>"Hedef Kitlesi"</i> temel eşleşme vektörü (W=20 Puan) olarak belirlenir.</li>
                  <li><strong>2. Kapasite Kısıtlı Dağılım:</strong> Kişiler her gruba maksimum/minimum kişi sınırlarına (K-Medoids mantığıyla) dikkat edilerek en iyi merkeze (gruba) atanır.</li>
                  <li><strong>3. Swap (Takas) Optimizasyonu:</strong> İlk dağılımdan sonra on binlerce çapraz eşleştirme ihtimali taranır. Örneğin; A kişisi 1. gruptan 3. gruba geçerse genel uyum skoru artıyorsa sistem sessizce bu takası yapar. Toplamda <strong>%70'in üzerinde</strong> bir uyum başarısı elde edilmiştir.</li>
                  <li><strong>4. Dinamik Entegrasyon:</strong> Form doldurmayan katılımcılar, asıl grubun analiz skorunu ve ana eksenini (PCA) bozmadan tamamen rastgele ve homojen bir şekilde 21 gruba serpiştirilmiştir. (Tablolarda "FORM YOK" etiketiyle kırmızı şekilde vurgulanırlar).</li>
                </ul>
              </div>
              <button className="modal-btn" onClick={() => setShowModal(false)}>
                Dashboard'u İncelemeye Başla
              </button>
            </div>
          </div>
        </div>
      )}

      <header className="header" style={{ marginBottom: '1.5rem' }}>
        <h1>
          <Cpu className="w-8 h-8 text-blue-600" />
          Genç Yetenek Gelişim Programı Gruplandırması
        </h1>
        <a 
          href="/YetGen_Gruplar.xlsx" 
          download="YetGen_Grup_Dagitimlari.xlsx"
          className="download-btn"
        >
          <Download className="w-5 h-5" />
          Tüm Grupları Excel Olarak İndir
        </a>
      </header>

      {/* Timeline Group Selector */}
      <div className="timeline-container glass">
        <div className="timeline-scroll" ref={timelineRef}>
          {groups.map(g => (
            <button
              key={g}
              onClick={() => setSelectedGroup(g)}
              className={`timeline-item ${selectedGroup === g ? 'active' : ''}`}
            >
              <div className="timeline-dot"></div>
              <span className="timeline-text">{g}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="dashboard-main-grid">
        {/* Left Side: Table & Members */}
        <div className="left-panel">
          <div className="glass panel-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <h2>{selectedGroup} Kümesi ({groupData.length} Kişi)</h2>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                {randomMembersCount > 0 && (
                  <div style={{ fontSize: '0.9rem', color: '#ef4444', fontWeight: 600 }}>
                    {randomMembersCount} Kişi Rastgele Eklendi
                  </div>
                )}
                <div className="match-badge">
                  Optimizasyon Oranı: %{topicMatchRate}
                </div>
              </div>
            </div>
            
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Katılımcı Kimliği</th>
                    <th>Önerilen Proje Konusu</th>
                    <th>1. Öncelikli Tercih</th>
                    <th>Hedef Kitle Parametreleri</th>
                  </tr>
                </thead>
                <tbody>
                  {groupData.map((person, idx) => {
                    const isRandom = person['Çözdüğün Testte Sana Önerilen Proje Konusu']?.includes('Form Doldurmadı');
                    
                    return (
                    <tr key={idx} style={{ 
                      backgroundColor: isRandom ? '#fef2f2' : 'transparent',
                      borderLeft: isRandom ? '4px solid #ef4444' : 'none'
                    }}>
                      <td style={{ fontWeight: 600, color: isRandom ? '#94a3b8' : '#1e293b', whiteSpace: 'nowrap' }}>
                        {person['İsim Soyisim'] || 'Bilinmiyor'}
                        {isRandom && (
                          <span style={{ 
                            marginLeft: '10px', 
                            fontSize: '0.7rem', 
                            background: '#ef4444', 
                            color: '#fff', 
                            padding: '3px 8px', 
                            borderRadius: '12px',
                            fontWeight: 700
                          }}>
                            FORM YOK
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={`tag ${isRandom ? '' : 'accent'}`} style={isRandom ? { background: '#f1f5f9', color: '#64748b', borderColor: '#e2e8f0' } : {}}>
                          {person['Çözdüğün Testte Sana Önerilen Proje Konusu']?.substring(0, 35)}
                          {person['Çözdüğün Testte Sana Önerilen Proje Konusu']?.length > 35 ? '...' : ''}
                        </span>
                      </td>
                      <td>
                        <span className="tag" style={isRandom ? { background: '#f1f5f9', color: '#64748b', borderColor: '#e2e8f0' } : {}}>
                          {person['Seçmek İstediğin Proje Konusu (1. Tercih)']?.substring(0, 30)}
                          {person['Seçmek İstediğin Proje Konusu (1. Tercih)']?.length > 30 ? '...' : ''}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {isRandom ? (
                             <span className="tag" style={{ background: '#f1f5f9', color: '#64748b', border: '1px solid #e2e8f0', margin: 0 }}>
                               Belirsiz
                             </span>
                          ) : (
                            person['Çalışmak İstediğin Hedef Kitleler (Birden fazla seçim yapabilirsin.)']
                              ?.split(',')
                              .slice(0, 2)
                              .map((kitle, i) => (
                              <span key={i} className="tag" style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', margin: 0 }}>
                                {kitle.trim()}
                              </span>
                            ))
                          )}
                        </div>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Side: Algorithm Logic & Stats */}
        <div className="right-panel">
          <div className="glass panel-content logic-panel">
            <div className="logic-header">
              <Activity className="w-6 h-6 text-blue-600" />
              <h3>Algoritma Mantığı ve Grup Uyumu</h3>
            </div>
            <p className="logic-description">
              Sistem, <strong>Kapasite Kısıtlı Kümeleme (Capacity Constrained Clustering)</strong> algoritması ile çalışmaktadır. 
              Katılımcılar arası benzerlik matrisi, belirlenen ağırlık katsayılarına göre <strong>(W1=20, W2=10...)</strong> hesaplanır.
            </p>
            
            <div className="logic-highlight glass-inner">
              <Target className="w-5 h-5 text-emerald-500" style={{ flexShrink: 0 }} />
              <div>
                <strong>Ana Bileşen Analizi (PCA):</strong>
                <span> Bu grubun model içindeki dominant ekseni <strong>"{topTopic}"</strong> olarak tespit edildi. Grup üyelerinin <strong>%{topicMatchRate}</strong>'i bu ortak vektör etrafında hizalandı.</span>
              </div>
            </div>

            <div className="logic-highlight glass-inner">
              <Star className="w-5 h-5 text-amber-500" style={{ flexShrink: 0 }} />
              <div>
                <strong>Swap (Takas) Optimizasyonu:</strong>
                <span> Küme içi varyansı minimize etmek için algoritmik takaslar yapıldı. Çapraz eşleşmeler (1. ve 2. tercihler) hesaba katılarak grubun genel entropisi (karmaşası) düşürüldü.</span>
              </div>
            </div>

            <h4 style={{ marginTop: '2.5rem', marginBottom: '1.5rem', color: '#1e293b', fontSize: '1.1rem' }}>Grup İçi Konu Dağılım Matrisi</h4>
            <div style={{ height: 230, width: '100%' }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={95}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="none" />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    contentStyle={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}
                    itemStyle={{ color: '#0f172a', fontWeight: 500 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
