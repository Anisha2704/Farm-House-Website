import axiosInstance from "./Axios";

const fetchData = async () => {
  try {
    const response = await axiosInstance.get('/menu');
    return response.data;
  } catch (error) {
    console.error("Error fetching data:", error);
    throw error;
  }
}

export default fetchData;