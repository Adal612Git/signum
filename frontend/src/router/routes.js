const routes = [
  {
    path: '/',
    component: () => import('layouts/GlobalLayout.vue'),
    children: [
      { path: '', component: () => import('pages/HomePage.vue') },
      { path: 'runs', component: () => import('pages/RunsPage.vue') },
      { path: 'exports', component: () => import('pages/ExportsPage.vue') },
      { path: 'preview', component: () => import('pages/PreviewPage.vue') },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
