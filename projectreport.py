import * as fs from 'fs';
import * as path from 'path';
import * as ts from 'typescript';

interface Component {
  name: string;
  filePath: string;
  selector: string;
  template: string;
  children: string[];
}

interface Pipe {
  name: string;
  filePath: string;
}

class ComprehensiveAngularProjectAnalyzer {
  private projectRoot: string;
  private output: string = '';
  private components: Map<string, Component> = new Map();
  private services: Set<string> = new Set();
  private modules: Set<string> = new Set();
  private pipes: Map<string, Pipe> = new Map();
  private routes: Map<string, string> = new Map();
  private dependencies: Map<string, Set<string>> = new Map();

  constructor(projectRoot: string) {
    this.projectRoot = projectRoot;
  }

  analyzeProject() {
    this.output += '# Angular Project Overview\n\n';
    this.analyzeProjectStructure();
    this.analyzeTypeScriptFiles(this.projectRoot);
    this.analyzeComponentRelationships();
    this.generateComponentTree();
    this.analyzePipes();
    this.analyzeDependencies();
    this.analyzeRouting();
    this.analyzeEnvironments();
    this.analyzeThirdPartyDependencies();
    this.analyzeTsConfig();
    
    return this.output;
  }

  private analyzeProjectStructure() {
    this.output += '## 1. Project Structure Overview\n\n```\n';
    this.output += this.getDirectoryStructure(this.projectRoot);
    this.output += '```\n\n';
  }

  private getDirectoryStructure(dir: string, prefix: string = ''): string {
    let result = '';
    const files = fs.readdirSync(dir);
    files.forEach((file, index) => {
      if (file.startsWith('.') || file === 'node_modules') return;
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      const isLast = index === files.length - 1;
      const marker = isLast ? '└── ' : '├── ';
      
      result += `${prefix}${marker}${file}\n`;
      
      if (stats.isDirectory()) {
        result += this.getDirectoryStructure(filePath, prefix + (isLast ? '    ' : '│   '));
      }
    });
    return result;
  }

  private analyzeTypeScriptFiles(dir: string) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
        this.analyzeTypeScriptFiles(filePath);
      } else if (path.extname(file) === '.ts') {
        this.analyzeTypeScriptFile(filePath);
      }
    });
  }

  private analyzeTypeScriptFile(filePath: string) {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const sourceFile = ts.createSourceFile(filePath, fileContent, ts.ScriptTarget.Latest, true);
    
    ts.forEachChild(sourceFile, node => {
      if (ts.isClassDeclaration(node)) {
        node.decorators?.forEach(decorator => {
          const decoratorName = decorator.expression.getText(sourceFile);
          if (decoratorName.startsWith('Component')) {
            this.analyzeComponent(node, sourceFile, filePath);
          } else if (decoratorName.startsWith('Injectable')) {
            this.analyzeService(node, sourceFile);
          } else if (decoratorName.startsWith('NgModule')) {
            this.analyzeModule(node, sourceFile);
          } else if (decoratorName.startsWith('Pipe')) {
            this.analyzePipe(node, sourceFile, filePath);
          }
        });
      }
    });

    if (filePath.endsWith('-routing.module.ts')) {
      this.extractRoutes(sourceFile);
    }

    this.analyzeDependenciesInFile(sourceFile);
  }

  private analyzeComponent(node: ts.ClassDeclaration, sourceFile: ts.SourceFile, filePath: string) {
    const name = node.name?.getText(sourceFile) || 'UnnamedComponent';
    let selector = '';
    let template = '';

    node.decorators?.forEach(decorator => {
      if (decorator.expression.getText(sourceFile).startsWith('Component')) {
        const args = (decorator.expression as ts.CallExpression).arguments;
        if (args.length > 0 && ts.isObjectLiteralExpression(args[0])) {
          args[0].properties.forEach(prop => {
            if (ts.isPropertyAssignment(prop)) {
              if (prop.name.getText(sourceFile) === 'selector') {
                selector = prop.initializer.getText(sourceFile).replace(/['"]/g, '');
              } else if (prop.name.getText(sourceFile) === 'template') {
                template = prop.initializer.getText(sourceFile).replace(/[`'"]/g, '');
              }
            }
          });
        }
      }
    });

    this.components.set(name, { name, filePath, selector, template, children: [] });
  }

  private analyzeService(node: ts.ClassDeclaration, sourceFile: ts.SourceFile) {
    const name = node.name?.getText(sourceFile) || 'UnnamedService';
    this.services.add(name);
  }

  private analyzeModule(node: ts.ClassDeclaration, sourceFile: ts.SourceFile) {
    const name = node.name?.getText(sourceFile) || 'UnnamedModule';
    this.modules.add(name);
  }

  private analyzePipe(node: ts.ClassDeclaration, sourceFile: ts.SourceFile, filePath: string) {
    const name = node.name?.getText(sourceFile) || 'UnnamedPipe';
    this.pipes.set(name, { name, filePath });
  }

  private extractRoutes(sourceFile: ts.SourceFile) {
    ts.forEachChild(sourceFile, node => {
      if (ts.isVariableStatement(node)) {
        const declaration = node.declarationList.declarations[0];
        if (ts.isVariableDeclaration(declaration) && declaration.initializer &&
            ts.isArrayLiteralExpression(declaration.initializer)) {
          declaration.initializer.elements.forEach(element => {
            if (ts.isObjectLiteralExpression(element)) {
              let path = '';
              let component = '';
              element.properties.forEach(prop => {
                if (ts.isPropertyAssignment(prop)) {
                  if (prop.name.getText(sourceFile) === 'path') {
                    path = prop.initializer.getText(sourceFile).replace(/'/g, '');
                  } else if (prop.name.getText(sourceFile) === 'component') {
                    component = prop.initializer.getText(sourceFile);
                  }
                }
              });
              if (path && component) {
                this.routes.set(path, component);
              }
            }
          });
        }
      }
    });
  }

  private analyzeDependenciesInFile(sourceFile: ts.SourceFile) {
    const filePath = sourceFile.fileName;
    const dependencies = new Set<string>();

    ts.forEachChild(sourceFile, node => {
      if (ts.isImportDeclaration(node)) {
        const moduleSpecifier = node.moduleSpecifier.getText(sourceFile).replace(/['"]/g, '');
        if (!moduleSpecifier.startsWith('.')) {
          dependencies.add(moduleSpecifier);
        }
      }
    });

    this.dependencies.set(filePath, dependencies);
  }

  private analyzeComponentRelationships() {
    this.components.forEach(component => {
      const componentSelector = component.selector;
      this.components.forEach(potentialParent => {
        if (potentialParent.template.includes(componentSelector)) {
          potentialParent.children.push(component.name);
        }
      });
    });
  }

  private generateComponentTree() {
    this.output += '## 2. Component Tree\n\n';
    const rootComponents = Array.from(this.components.values()).filter(component => 
      !Array.from(this.components.values()).some(c => c.children.includes(component.name))
    );
    rootComponents.forEach(component => {
      this.output += this.generateComponentTreeRecursive(component, 0);
    });
    this.output += '\n';
  }

  private generateComponentTreeRecursive(component: Component, depth: number): string {
    let result = `${'  '.repeat(depth)}- ${component.name}\n`;
    component.children.forEach(childName => {
      const childComponent = this.components.get(childName);
      if (childComponent) {
        result += this.generateComponentTreeRecursive(childComponent, depth + 1);
      }
    });
    return result;
  }

  private analyzePipes() {
    this.output += '## 3. Pipes\n\n';
    this.pipes.forEach(pipe => {
      this.output += `- ${pipe.name} (${pipe.filePath})\n`;
    });
    this.output += '\n';
  }

  private analyzeDependencies() {
    this.output += '## 4. Dependencies\n\n';
    this.dependencies.forEach((deps, filePath) => {
      this.output += `### ${path.relative(this.projectRoot, filePath)}\n`;
      deps.forEach(dep => {
        this.output += `- ${dep}\n`;
      });
      this.output += '\n';
    });
  }

  private analyzeRouting() {
    this.output += '## 5. Routing Configuration\n\n';
    this.routes.forEach((component, path) => {
      this.output += `- /${path} -> ${component}\n`;
    });
    this.output += '\n';
  }

  private analyzeEnvironments() {
    this.output += '## 6. Environment Configurations\n\n';
    const envPath = path.join(this.projectRoot, 'src', 'environments');
    if (fs.existsSync(envPath)) {
      fs.readdirSync(envPath).forEach(file => {
        if (file.startsWith('environment') && file.endsWith('.ts')) {
          this.output += `- ${file}\n`;
        }
      });
    }
    this.output += '\n';
  }

  private analyzeThirdPartyDependencies() {
    this.output += '## 7. Third-party Dependencies\n\n';
    const packageJsonPath = path.join(this.projectRoot, 'package.json');
    if (fs.existsSync(packageJsonPath)) {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
      this.output += 'Dependencies:\n';
      for (const [dep, version] of Object.entries(packageJson.dependencies || {})) {
        this.output += `- ${dep}: ${version}\n`;
      }
      this.output += '\nDev Dependencies:\n';
      for (const [dep, version] of Object.entries(packageJson.devDependencies || {})) {
        this.output += `- ${dep}: ${version}\n`;
      }
    }
    this.output += '\n';
  }

  private analyzeTsConfig() {
    this.output += '## 8. TypeScript Configuration\n\n';
    const tsConfigPath = path.join(this.projectRoot, 'tsconfig.json');
    if (fs.existsSync(tsConfigPath)) {
      const tsConfig = JSON.parse(fs.readFileSync(tsConfigPath, 'utf8'));
      this.output += '```json\n';
      this.output += JSON.stringify(tsConfig, null, 2);
      this.output += '\n```\n\n';
    }
  }
}

// Usage
const projectRoot = process.argv[2] || '.';
const analyzer = new ComprehensiveAngularProjectAnalyzer(projectRoot);
const projectOverview = analyzer.analyzeProject();
fs.writeFileSync('project-overview.md', projectOverview);
console.log('Project analysis complete. Results written to project-overview.md');
