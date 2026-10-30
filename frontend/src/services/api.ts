import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:5001/api/v1'});
api.interceptors.request.use(c=>{const t=localStorage.getItem('aeronex_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c;});
export default api;
