import React, { useState, useEffect } from 'react';

export default function ChatBot() {
  const [q, setQ] = useState('');
  const [ans, setAns] = useState('');
  const [sel, setSel] = useState('');

  useEffect(() => {
    const h = () => setSel(window.getSelection()?.toString() || '');
    document.addEventListener('mouseup', h);
    return () => document.removeEventListener('mouseup', h);
  }, []);

  const send = async () => {
    setAns('Thinking...');
   try {
  const res = await fetch('http://127.0.0.1:8000/query',{
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      question: q,
      selected_text: sel
    })
  });



      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      setAns(data.answer);
    } catch (error) {
      console.error('Error:', error);
      setAns('Error occurred while processing your request.');
    }
  };

  return (
    <div style={{position:'fixed',bottom:20,right:20,width:380,background:'white',border:'3px solid #0066ff',borderRadius:15,padding:15,boxShadow:'0 0 30px rgba(0,100,255,0.4)',fontFamily:'Arial',zIndex:9999}}>
      <h3>AI Tutor</h3>
      {sel && <p>Selected text used</p>}
      <textarea value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask anything..." style={{width:'100%',height:80}} />
      <button onClick={send} style={{marginTop:8,padding:'10px 20px',background:'#0066ff',color:'white',border:'none',borderRadius:8}}>Send</button>
      <div style={{marginTop:15,padding:15,background:'#f0f8ff',borderRadius:8,maxHeight:300,overflow:'auto'}}>{ans}</div>
    </div>
  );
}