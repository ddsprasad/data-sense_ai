export const VaiableConstants = {
  SOMETHING_WENT_WRONG: 'Oops! We encountered an unexpected issue while processing your request. Please rephrase your query and try again, or contact support if the problem continues.',
  APEXTOOLBAR: {
    show: true,
    offsetX: 0,
    offsetY: 0,
    tools: {
      download: true,
      selection: true,
      zoom: true,
      zoomin: true,
      zoomout: true,
      pan: true,
      customIcons: <any>[
        {
          // icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-maximize-2"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>',
          icon: '<svg width="15" height="16" viewBox="0 0 15 16" fill="none" xmlns="http://www.w3.org/2000/svg"> <path d="M13.4428 8.40606V14.7293C13.4428 15.0203 13.2159 15.2562 12.9361 15.2562H0.775748C0.495911 15.2562 0.269043 15.0203 0.269043 14.7293V2.08274C0.269043 1.79174 0.495911 1.55581 0.775748 1.55581H6.8559C7.13574 1.55581 7.3626 1.79174 7.3626 2.08274C7.3626 2.37374 7.13574 2.60968 6.8559 2.60968H1.28239V14.2023H12.4294V8.40606C12.4294 8.11507 12.6563 7.87913 12.9361 7.87913C13.2159 7.87913 13.4428 8.11507 13.4428 8.40606ZM12.5454 4.29972L10.9779 2.66955L5.53973 8.32507L5.10858 10.4037L7.10728 9.95531L12.5454 4.29972ZM14.5974 2.16563L13.0299 0.535461L11.7686 1.84719L13.3361 3.47734L14.5974 2.16563Z" fill="#514F4F"/> </svg>',
          title: 'Edit Chart',
          index: 0, // Adjust this index based on your needs
          class: 'custom-apex-icon',
        }
      ]
    },
  },
  GOOGLECHARTOPTIONS: {
    region: 'US',
    displayMode: 'markers',
    resolution: 'provinces',
    colorAxis: { colors: ['#0087ff', '#ff7800'] },
    enableRegionInteractivity: true,
    backgroundColor: '#81d4fa',
    datalessRegionColor: '#fff',
    chartArea: { 'width': '100%', 'height': '100%' },
    responsive: true
  }
}


