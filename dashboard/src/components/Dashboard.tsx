import { useState, useEffect, useRef } from 'react';
import Papa from 'papaparse';
import { Target, Star, Cpu, Download, X } from 'lucide-react';

interface Participant {
  'Grup No': string;
  'İsim Soyisim': string;
  'Çözdüğün Testte Sana Önerilen Proje Konusu': string;
  'Seçmek İstediğin Proje Konusu (1. Tercih)': string;
  'Seçmek İstediğin Proje Konusu (2. Tercih)': string;
  'Seçmek İstediğin Proje Konusu (3. Tercih)': string;
  'Çalışmak İstediğin Hedef Kitleler (Birden fazla seçim yapabilirsin.)': string;
  'Atanan Konu'?: string;
  'Atanan Hedef Kitle'?: string;
}



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
                Tüm katılımcılar analiz edildi ve gruplar başarıyla oluşturuldu! Toplam 7 proje konusunun her birinden tam <strong>3'er grup</strong> oluşturularak 21 grup dengeli bir şekilde dağıtılmıştır.
              </p>
              <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#1e293b' }}>⚙️ Algoritma Nasıl Çalışıyor?</h3>
                <ul style={{ paddingLeft: '1.5rem', color: '#475569', lineHeight: 1.8 }}>
                  <li><strong>1. Sabit Profil Ataması:</strong> Oluşturulan 21 gruba spesifik bir Proje Konusu ve Hedef Kitle baştan atanmıştır.</li>
                  <li><strong>2. Çekim Gücü ve Eşleşme:</strong> Algoritma kişileri dağıtırken, katılımcının tercih ettiği konu ile grubun atanan konusu örtüşüyorsa çok yüksek bir bonus eşleşme puanı (+30) verir. Böylece kişiler odaklanmak istedikleri alana yönlendirilir.</li>
                  <li><strong>3. Kapasite Kısıtlı Kümeleme:</strong> Her grubun eşit sayıda katılımcı barındırması için maksimum grup boyutları sıkı bir şekilde sınırlandırılmıştır.</li>
                  <li><strong>4. Entropi Düşürme:</strong> Katılımcıların 1., 2. ve 3. tercihleri gibi yan değişkenler de hesaba katılarak, kapasite sebebiyle oluşan zorunlu kaydırmalarda grup uyumu en az zarar görecek şekilde optimize edilmiştir.</li>
                </ul>
              </div>
              <button className="modal-btn" onClick={() => setShowModal(false)} style={{ marginTop: '1.5rem' }}>
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

      <div className="dashboard-main-content">
        {/* Full Width: Table & Members */}
        <div className="left-panel" style={{ width: '100%' }}>
          <div className="glass panel-content">
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid #e2e8f0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h2 style={{ fontSize: '1.5rem', color: '#0f172a', margin: 0 }}>{selectedGroup} Kümesi ({groupData.length} Kişi)</h2>
              </div>
              
              {/* Group Profile Header */}
              {groupData.length > 0 && groupData[0]['Atanan Konu'] && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#eff6ff', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                    <Target className="w-5 h-5 text-blue-600" />
                    <span style={{ color: '#475569', fontWeight: 600 }}>Konu:</span>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>{groupData[0]['Atanan Konu']}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#fef3c7', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid #fde68a' }}>
                    <Star className="w-5 h-5 text-amber-600" />
                    <span style={{ color: '#475569', fontWeight: 600 }}>Hedef Kitle:</span>
                    <span style={{ color: '#1e293b', fontWeight: 700 }}>{groupData[0]['Atanan Hedef Kitle']}</span>
                  </div>
                </div>
              )}
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


      </div>
    </div>
  );
}
