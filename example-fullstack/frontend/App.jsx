import React, { useState, useEffect } from 'react';
import axios from 'axios';
import _ from 'lodash';

function App() {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Example using axios
    axios.get('/api/data')
      .then(response => {
        // Example using lodash
        const processed = _.map(response.data, item => item.value);
        setData(processed);
      });
  }, []);

  return (
    <div>
      <h1>Fullstack Example</h1>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}

export default App;
