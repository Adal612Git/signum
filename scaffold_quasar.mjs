import prompts from 'prompts'

// Pre-answer all prompts with defaults for a minimal SPA
// See create-quasar source for keys used
const scope = {
  projectFolder: 'frontend',
  projectFolderName: 'frontend',
  projectType: 'app',
  scriptType: 'js',
  engine: 'vite-2',
  name: 'frontend',
  productName: 'Quasar App',
  description: 'A Quasar Project',
  author: 'Signum <signum@example.com>',
  sfcStyle: 'composition-setup',
  css: 'scss',
  preset: { eslint: true },
  prettier: true,
  packageManager: 'npm',
  overwrite: true,
}

prompts.override(scope)

// Importing the bin runs it with our overrides
await import('create-quasar')
