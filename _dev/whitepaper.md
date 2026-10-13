# hx+: A Community Superset of Haxe

*Draft for community review. The language is written hx+. In package names, URLs and other ASCII-only places it's hxplus.*

---

## Summary

hx+ is a strict superset of Haxe 4.3. It's built on hxc, a faithful Haxe compiler written in Haxe and checked byte for byte against the reference compiler. Any valid Haxe 4.3 program is a valid hx+ program and behaves the same way.

On top of that base, hx+ adds language features people have been asking for for years, adds new standard library packages next to the existing ones without replacing them, and changes how targets get added. In hxc a target is ordinary Haxe code, so keeping Haxe on every platform stops depending on a handful of maintainers. And it aims to let Haxe ship as libraries other ecosystems depend on, not only as whole applications.

This document covers why we built it, how compatibility is kept, what hx+ adds, how the project is run, and where things stand today. hxc itself is out now: `haxelib install hxc`.

---

## 1. Why the target list matters

Haxe was built on one idea: write the code once and ship it to the web, desktop, mobile and servers. That's why the biggest projects in the ecosystem exist. It's what Lime and OpenFL, the frameworks we maintain, were built around, and today they're the [two most downloaded libraries on haxelib](https://lib.haxe.org/) at roughly two million downloads each. We're writing this as the people responsible for that user base.

For the teams and businesses that ship on Haxe, the target list is the reason they picked it. Plenty of modern languages have nice syntax. Very few reach as many platforms from one codebase.

There's a longer-term reason too. Haxe doesn't build its own runtimes. Like TypeScript on JavaScript engines and Kotlin on the JVM, it runs on runtimes other people build and maintain: their garbage collectors, JITs, debuggers and platform ports. That's the only model that works for a language Haxe's size. The risk is that when a host platform dies, code that can only run there dies with it. Haxe has already been through that once. It started in the Flash era and outlived Flash because the same code could move to other targets. Every target Haxe supports is another host it can fall back on, and every target it drops puts more weight on the ones that are left.

## 2. Where upstream is going

The upstream project is consolidating. [Haxe 5.0.0-preview.1](https://github.com/HaxeFoundation/haxe/releases/tag/5.0.0-preview.1) (July 2025) removed the C# and Java targets and 32-bit Windows support, and moved parts of the standard library (`sys.db`, `haxe.remoting`, `php.Web`) out to a compatibility library. [Haxe 4.3 is the last release with the removed targets](https://community.haxe.org/t/haxe-4-3-7-released/4611). The big investments on the 5.x side, [asys](https://github.com/HaxeFoundation/haxe-evolution/blob/master/proposals/0010-asys.md) and coroutines, are good additions, but other languages already have them. They don't add reach.

We're grateful to everyone who has built and maintained Haxe over the last twenty years, and this document isn't a criticism of anyone. Keeping targets alive in the upstream codebase takes real effort, and cutting them is a reasonable response to that. We think the cost can be brought down, so we built a compiler where it is.

## 3. hxc: a Haxe compiler, written in Haxe

The canonical Haxe compiler is written in OCaml. To work on it you need to know Haxe deeply and also be comfortable in OCaml, and historically that's been a small group of people. When keeping a target alive requires someone from that group, targets live or die with whoever happens to maintain them. Target removals come out of that situation.

hxc is a faithful Haxe 4.3 compiler, written in Haxe:

- **We test against the reference compiler.** We don't judge hxc's correctness ourselves. It's tested against the real `haxe` 4.3.7 binary using Haxe's own test suites, and the outputs are compared byte for byte.
- **It builds with the normal toolchain** (haxe and hxcpp) into a native binary, and it can rebuild itself.

The result behaves like Haxe 4.3: same command line, same hxml files, same output, same display protocol for editors. The difference is that the compiler is written in the language its users already write every day. If you hit a compiler bug, you can open the compiler in the same editor and debugger you use for your own project, and far more people can contribute to it.

Haxe written in Haxe isn't a new idea. Nicolas Cannasse opened [Haxe-in-Haxe notes](https://github.com/HaxeFoundation/haxe/issues/6843) in 2018, and it's still open. Over the years that thread asked for what hxc is built for: a compiler more people can work on, compiling in the browser, adding targets without OCaml, and running real Haxe as a script inside an app. It's part of why we started.

### Self-hosting

Most serious languages get here eventually:

| Language | Original compiler | Self-hosted |
|---|---|---|
| C | assembly / earlier B | self-hosted since the 1970s |
| Rust | OCaml ("rustboot") | [rustc, self-compiling since 2011](https://www.languagelineage.org/languages/rust) |
| Go | C | [entirely Go as of Go 1.5 (2015)](https://www.infoq.com/news/2015/08/go-1-5) |
| C# | C++ | Roslyn, C# in C# (2014) |
| Kotlin | Java | compiler written in Kotlin |
| Haxe | OCaml | hxc |

Rust is a good example. Its first compiler was written in OCaml, and it was replaced once Rust could compile itself.

TypeScript went the other way. In 2025 Microsoft [ported the TypeScript compiler from TypeScript to Go](https://devblogs.microsoft.com/typescript/typescript-native-port/) for roughly a 10x speedup. The reason is specific to TypeScript: it compiles to JavaScript, so its compiler always ran on a JavaScript engine. Haxe compiles to native code through hxcpp, so hxc is self-hosted and still a native binary.

### Adding targets

Every generator in hxc is ordinary Haxe code. That alone makes targets much cheaper to write and keep alive than they are in OCaml, and it's how hxc already covers eval and macros, JavaScript, C++, cppia and JVM bytecode, with an experimental Rust backend alongside them.

The next step is a single interface for targets, which is designed and under way. A target becomes a package of Haxe source compiled into hxc. It declares what it supports up front (overloads, how closures capture variables, its analyzer and optimizer rules and so on), adds its own filter passes at named points in the pipeline, and supplies its generator and its build step, which is where it picks its own runtime and toolchain. The typer and optimizer read those declarations instead of checking which target is selected, and the built-in targets go through the same interface as anyone else's. The declarations are plain values set once before typing, so a plugged-in target compiles as fast as a built-in one.

A new target reports the nearest existing platform for conditional compilation and identifies itself by name, so existing `#if` code keeps working. Target authors get the tools the built-in targets already use (typed-tree printers, the lowering passes, name mangling, the source-map writer) and a test command that runs Haxe's unit suite against their target or compares two targets' output. C++ moves behind the interface first, then the other built-in targets, and after that the interface opens to targets that live in their own haxelibs, with a version number from then on.

So adding a target doesn't need OCaml, and the maintenance falls on the people who need that target and nobody else. Every target is measured the same way: it's conformant when it passes Haxe's own test suite for that target. The Target SDK on the roadmap is this interface plus documentation, scaffolding and the conformance harness, so adding targets isn't limited to us. Upstream added a "Custom" target hook in Haxe 5, which points at the same need.

### A second C++ backend

C++ goes first for a reason. Once it's behind the interface, a second C++ backend can grow next to the current one instead of replacing it in place. The new backend starts out producing the same code as the current one and then changes on purpose, with the current one as its live reference: Haxe's unit suite, the hxcpp test suites and the Lime and OpenFL samples run under both, and the results are compared.

It pairs with a runtime of its own, which makes changes possible that need both sides at once. One example is the generator emitting precise GC roots instead of the runtime scanning the stack conservatively. It reports itself as C++, so `#if cpp` code in Lime, OpenFL and native extensions compiles unchanged, and anything the ecosystem relies on today (`Build.xml`, CFFI, the `hx/*.h` headers, the `cpp.*` externs) only changes behind defines until the ecosystem moves with it.

## 4. Libraries, not just applications

Haxe's reach has a limit, and it isn't the number of targets. It's where Haxe can sit in a project. Today Haxe has to be the top layer. You write the application in Haxe and the compiler produces a self-contained bundle with its own runtime and standard library. You can pull native or JavaScript libraries in underneath, but Haxe has to be on top.

Rust doesn't have that limit. It can be a binary, a WebAssembly module, the native core of a Python package, or just a library another project depends on. That's a big part of how it spreads: people add it to existing projects instead of rewriting projects in it.

For Haxe, "write once, run everywhere" works at the application level, which is where every ecosystem's tools and habits are hardest to change. Adopting Haxe usually means moving your project under Haxe instead of adding Haxe as one more dependency, and that's a real cost to adoption.

hx+ aims to remove it by changing what the compiler can emit: library code that fits into the host ecosystem like any other package, without bundling its own runtime.

- **ESM JavaScript.** Externs become normal ES imports, and the standard library ships as a real npm package, `@haxeorg/std`. Generated code imports the std instead of bundling it, so ten Haxe libraries in one project share one copy. A TypeScript user runs `npm install`, gets a typed dependency, and doesn't need to know it was written in Haxe.
- **Rust.** `haxe-std` as a crate on crates.io, and generated crates that depend on it, so a Rust project can `cargo add` a library written in Haxe.

Three things have to hold for this to work:

- **A stable standard library.** People can only depend on `@haxeorg/std` if it doesn't keep changing under them. The compatibility rules in section 5 are what make that possible.
- **Typed public APIs.** `Dynamic` and reflection stay inside the library, and what consumers see is normal, typed host-language API. Otherwise nobody would want to depend on it.
- **Doing it in order.** ESM on npm comes first. Kotlin/JS and Scala.js already produce JavaScript other projects can use, so this is engineering work, not research. Native crates take longer, because Haxe assumes garbage collection, and a library has to give its consumers a memory model they can live with even if they never chose that runtime.

This is a big part of why we wrote the compiler in Haxe in the first place. Library output means a lot of ongoing, target-specific generator work: shaping ESM, keeping extern imports, linking the std as an external package and keeping the public API typed, across many targets at once. That kind of work only keeps getting done if a lot of people can contribute to the compiler.

## 5. A superset, not a fork

hx+ is a strict superset of Haxe 4.3: every valid Haxe 4.3 program is a valid hx+ program and behaves the same. That's tested, because hxc is checked against the reference 4.3 compiler.

Our compatibility rules:

1. **Haxe 4.3 code keeps working.** It compiles on hx+ unchanged and behaves the same. The 4.3 edition is a fixed thing with a fixed test suite, which is what makes the promise affordable to keep. The other direction, hx+ code compiling on the canonical compiler, isn't required, but we plan a transpile-to-Haxe mode so hx+ code can still go back into normal Haxe projects.
2. **The existing standard library stays.** For code on the 4.3 edition, existing APIs aren't changed or removed. When an existing design can't be fixed (networking, below), the replacement goes next to it in a new package, and the old API is marked deprecated, which is a warning and never a break.
3. **Changes are opt-in.** New syntax uses contextual keywords, so nothing that's a valid identifier today stops being one. Stricter checking is behind flags.
4. **Editions for the long term.** Borrowed from [Rust's edition system](https://doc.rust-lang.org/edition-guide/): a per-module language version. Code written against the 4.3 edition keeps compiling in the same build as code written against newer editions, and nobody is forced to migrate. Editions are also how hx+ moves forward: a newer edition can change defaults or drop deprecated APIs, and only the modules that opt into it see the change.
5. **Exceptions are listed ahead of time.** Like [Go's compatibility promise](https://go.dev/doc/go1compat), which has held for over a decade because its exceptions were spelled out up front, the few cases that can change behavior are published in advance: security and soundness fixes (with a define to restore the old behavior where possible), and APIs whose platform drops a capability, which keep compiling even if the platform no longer supports them at runtime. Nothing outside that list breaks compatibility.

We picked these rules by looking at how other projects handled situations like this one. Compatible continuations tend to help an ecosystem, and incompatible breaks tend to split it. egcs stayed compatible with GCC and ended up becoming GCC. io.js stayed compatible with Node.js and merged back within a year. MariaDB worked as a drop-in for MySQL, so people could switch without a split. We want the same options open for hx+, including merging work back if upstream ever wants it.

## 6. What hx+ adds

hx+ features fall into three groups, and each is tested differently.

### Syntax that lowers to Haxe

New syntax is rewritten into plain Haxe 4.3 right after parsing, before typing and before macros run, wherever that can be done correctly and efficiently. Existing macro libraries see ordinary Haxe and keep working. Each of these features is tested by printing the rewritten program as Haxe and checking that the reference compiler produces the same result. The few features that need deeper compiler support are tested on behavior instead.

The first two:

- **`try` / `catch` / `finally`.** People have asked for this for more than ten years. `finally` is a contextual keyword. It's also the main exception to the rewrite rule, because a correct and efficient `finally` can't be done by rewriting source (rethrows and exception overhead get in the way). So it's built into the compiler and lowered per target: native `finally` where the platform has one, and the usual exit-path lowering where it doesn't, the same way C# and Java compilers handle it. Features that need this kind of compiler work are rare, and each one has to make the case for it in its RFC.
- **`const`.** A `const` initializer is evaluated at compile time and inserted as a literal, which `final` doesn't guarantee. The evaluation uses the compiler's existing macro interpreter.

### Compile-time features

Features run by the compiler's built-in evaluator, the same one that runs macros: `const` evaluation above and, later, more compile-time programming. These can still be checked against the reference compiler, since what they produce is standard Haxe.

### Standard library additions

New APIs only, next to the existing 4.3 std, with their own test suite. Networking is the main example. `sys.net.Host` stores an address as a single `Int`, so it can't hold an IPv6 address. Instead of patching it, hx+ leaves `sys.net` as the legacy IPv4 API and adds a new dual-stack networking package. Where upstream's asys design is good, we plan to match its API so code written against it stays source-compatible.

Coroutines and structured async, the main features on upstream's roadmap, are candidates for hx+ too, on the 4.3 base and on our own schedule, without giving up any targets.

### The candidate list

Past the first features there's a list of candidates waiting for the RFC process. Each one has been checked against the same rules: it rewrites cleanly, uses contextual keywords only, and only adds to the std.

- **Syntax:** tuples with destructuring and multiple return values, asked for as far back as [#4300](https://github.com/HaxeFoundation/haxe/issues/4300) and [#5114](https://github.com/HaxeFoundation/haxe/issues/5114), first lowered to generated value classes and later, as the optimizer improves, allocation-free where they don't escape; `using` declarations and `defer`, both built on the same machinery as `finally` (whose own request, [#3335](https://github.com/HaxeFoundation/haxe/issues/3335), dates to 2015); a cascade operator (`..`) for configuring objects; `let`-`else` bindings (destructure an enum or return early without a full switch); a pipe operator (`|>`); safe casts (`as?`, returning null instead of throwing); opaque typedefs (a one-keyword version of the abstract wrapper everyone writes by hand); property shorthand; methods on enums; range checks and range slicing; raw string literals; tagged string templates for typed DSLs; digit separators and binary literals (binary literals come from Haxe 5).
- **Compile time:** records with generated structural equality, hashing and copying, built the same way as `const`; `static assert`; `nameof` (identifier strings that survive refactoring); compile-time file embedding; general compile-time evaluation through the eval engine; and method contracts (`requires`/`ensures`, proposed in [#8905](https://github.com/HaxeFoundation/haxe/issues/8905)), in runtime and debug modes first, with static checking later.
- **Standard library:** a new date and time package (same approach as networking, because `Date` needs it); WebSockets, TLS and modern crypto as part of the new networking package; sized number types (`u8` through `i64`, `f32`) with better binary data handling, which game and network code needs all the time; BigInteger, from Haxe 5; proper Unicode utilities; a standard test runner.

Almost everything on this list comes from requests in the Haxe issue tracker, some of them open for ten years. None of it is a commitment. The RFC process is where these get ranked, changed or turned down, in public.

### Tooling

The things that push teams off Haxe usually aren't syntax, so hx+ treats tooling as real work:

- **Dependency management.** haxelib installs globally and has no lockfiles or reproducible builds, and the community has built its own replacements because of it. hx+ will have per-project, lockfile-based, reproducible dependencies, with a registry that tracks compatibility.
- **Better diagnostics.** Rust showed that error messages are part of the product: explanations, suggestions, and error codes with documentation pages. A compiler being written now can start at that level. The same structured diagnostics that help people fix their code also help AI tools (section 7).
- **Null safety through an edition.** Haxe's current null safety is experimental and hard to use against the standard library. Null safety that actually holds is a type-system change, which makes it the obvious first use of editions: a future edition where code is null-safe by default, adopted one module at a time. Other type-system features follow it, some as additions to the typer and some through editions: named arguments and named-only parameters ([#4507](https://github.com/HaxeFoundation/haxe/issues/4507)), union types with flow narrowing ([#4281](https://github.com/HaxeFoundation/haxe/issues/4281)), overloading for ordinary classes, and narrowing after `is` checks.
- **A REPL.** Haxe has never had an official one. hx+ has an eval engine built in, so it will, along with watch-mode builds and hot-reloadable scripting.
- **hxia.** A scripting layer for shipped applications, built alongside the compiler. One compiled artifact loads into both the native and the web build of the same program. The runtime is Haxe compiled into the host, so script values are host values: host arrays, strings and closures, the host's garbage collector, no marshalling and no second heap. Untrusted content runs in a metered sandbox, where the compiler and the host control what it can reach; trusted content can use the fastest engine the platform has. For the kind of things this ecosystem ships, that means mods, plugins and live content that work on every target.
- **The rest:** an official code formatter; a standard derive framework for serialization, equality and introspection, so projects stop writing the same macros; a standard HTTP client and server on the new networking package; and eventually a written language specification, which Haxe has never had and which the conformance work already points toward.

## 7. AI

We think Haxe has an advantage here that hasn't gotten much attention. More and more code is written with AI tools involved, and those tools do worse when a project is spread across several languages, because every boundary between languages is another place to make mistakes. A single language that targets web, native, mobile and servers keeps all of that in one type system and one standard library.

That only helps if the tooling is good, so we're working on:

- **Structured compiler output.** hxc produces machine-readable diagnostics (the same JSON used for editor support), so the write, compile and fix loop is fast and exact.
- **A toolchain you already have.** OCaml is hard to set up, for people and for AI agents alike, and an agent that can't build the compiler can't test its own changes. hxc builds with the haxe and hxcpp every Haxe user already has.
- **Mechanical verification.** Because hxc is checked against the reference compiler, contributions, including AI-assisted ones and entire targets, are tested instead of trusted on sight. That's what makes AI-assisted compiler work safe.
- **A sandbox.** The [haxe.run](https://haxe.run) playground compiles and runs Haxe in the browser, and tools can drive it as well as people.
- **Documentation sized for models.** The language spec, the std and common patterns packaged so current models can write good hx+ without waiting to be trained on it.

AI doesn't automatically favor small languages. It favors languages with a good feedback loop, and that's a tooling problem we can work on.

## 8. Stewardship and governance

We maintain Lime and OpenFL, the most depended-on consumer frameworks in the ecosystem. Hundreds of shipped games and apps, and the people who make a living from them, depend on the Haxe 4.x line. We built hxc and hx+ because we're responsible for that user base, and its foundation shouldn't depend on decisions made somewhere else under constraints we don't share.

That said, hx+ isn't built for OpenFL. It's meant to belong to the community:

- **Open RFCs.** Every language proposal is public, and each one comes with a working haxe.run link so people can try it instead of imagining it. hx+'s own first features, `finally` and `const`, will be the first RFCs, discussed in public before they're final.
- **A compiler people can work on.** It's written in Haxe. If you write Haxe, you can read, debug and improve it.
- **Targets belong to the people who use them.** The Target SDK is there so the people who need a platform can maintain it. Conformance is measured by the public test suite, not by anyone's sign-off.
- **Compatibility as a commitment.** The 4.3 edition is a standing promise, and its exceptions are written down in advance. The project only works if it doesn't break the code of the people who rely on it.

hx+ doesn't take anything away from anyone. Haxe 4.3 code keeps a future, Haxe 5 continues on its own path, features that prove themselves in hx+ are there for upstream to adopt, and every hx+ program is still a Haxe program. We want hx+ to add to the ecosystem without splitting it, and we expect to be held to that.

### Licensing

The hx+ toolchain is released under the Mozilla Public License 2.0 (MPL-2.0) wherever the code is ours to license: the hx+ language layer, the new standard library packages, the Target SDK and new backends, and the project's tooling. We picked it for three reasons:

- **File-level copyleft.** Changes to the toolchain's own files have to be shared back, so improvements to the compiler stay open.
- **Nothing reaches into your code.** Applications built with hx+, and products or engines that embed the toolchain, take on no obligations for their own code. That matters because embedding is a core use case: a game or app should be able to ship the compiler inside it, compiling and loading scripts at runtime, without its own code taking on copyleft obligations. For commercial studios, that decides whether they can use it at all.
- **Nothing is closed off to upstream.** MPL-2.0 code can be used in GPL projects, so anything we build can go into the canonical compiler if upstream wants it.

Where code comes from upstream sources, it keeps the license it came with: the canonical compiler's sources are GPL and the standard library is MIT. We're finalizing the exact license boundaries with counsel so every upstream obligation is met.

## 9. Where things stand

The earliest prototypes of this work go back to the Haxe 3 era. Here's where it is today:

- hxc 0.6.6 is on haxelib. Install it with `haxelib install hxc` and run it with `haxelib run hxc` wherever you'd run haxe. The package includes the compiler for Windows x64; other platforms build from source for now.
- An 18-gate parity battery checks hxc against the reference compiler, Haxe 4.3.7. It covers Haxe's unit suite, with JavaScript and C++ output compared byte for byte across every dead-code and analyzer setting; the unit, sys and threads suites under the interpreter; every hxcpp test suite; the compilation server; and hxc rebuilding its own source. As of October 2026 every gate passes.
- hxc compiles itself, and the compiler it builds produces identical output when it compiles itself again.
- It builds Lime and OpenFL applications.
- It generates JVM bytecode alongside JavaScript, C++ and cppia, and the Rust backend runs experimentally.
- Compiled to WebAssembly, hxc runs in the browser. The [haxe.run](https://haxe.run) playground is built on that, and it's live.
- hxia runs: a mod compiled once loads into the C++ build and the JavaScript build of the same game and plays the same in both.
- The target interface from section 3 is designed and under way, starting with C++.
- The hx+ language features and the new networking package are designed and specified, but not shipped yet.

The phases below are ordered by dependency: the playground needs the JavaScript backend, the Target SDK needs the parity base, and Unity needs the C# target. Each phase ships something usable on its own.

### Phase 1: hxc parity

Parity with the reference Haxe 4.3 compiler, target by target: eval and macros, then JavaScript, then C++ and cppia. The gates are mechanical: Haxe's unit suite at zero failures per target, compiler messages byte for byte, and Lime and OpenFL building and running unmodified. hx+ features only land after this.

### Phase 2: In the browser

The compiler, compiled to WebAssembly, running client-side at haxe.run: write Haxe, compile it, run it, share it. Structured diagnostics land here, since the playground uses them. This is also when this document and the community spaces go public, with the playground showing that it works. Done when the playground compiles and runs real programs in the browser.

### Phase 3: hx+ 1.0

The edition mechanism, with 4.3 as the permanent base edition; `finally` and `const` as the first RFCs, with live playground demos; the transpile-to-Haxe mode; and the Target SDK with its conformance harness, built on the target interface that C++ moves behind first. The Rust backend ships as a preview of what the SDK makes possible. Done when hx+ programs compile, the rewrites check out against the reference compiler, and the first RFC comes from someone outside the project.

### Phase 4: The platform

The things that keep teams around, in order of how much they hurt today: the new networking package (IPv6, TLS, HTTP, WebSockets); the package manager (per-project, lockfiles, reproducible, with a haxelib bridge from day one); the official REPL; and hxia in shipped applications. Features from the RFC list start landing on a regular schedule. Done when a team can build, manage dependencies, test and deploy on hx+ without the old tooling.

### Phase 5: More targets

- **Library output**, as described in section 4: ESM JavaScript that imports `@haxeorg/std` from npm instead of bundling a runtime, then Rust crates that depend on `haxe-std`.
- **A second C++ backend**, next to the current one and with a runtime of its own (section 3).
- **Rust**, to full conformance. It's the first new backend in the ecosystem in years and the proof that the Target SDK works. Besides its own uses (WebAssembly, embedded, servers), it shows a target can be added because the architecture made it cheap.

- **New C# and Java targets.** Haxe 5 removed both, and [the community asked for C# back right away](https://community.haxe.org/t/a-new-c-target-for-haxe-5/4764). Instead of reviving generators written for older versions of both platforms, hx+ plans new backends: C# for modern .NET (current runtime and interop, NativeAOT-aware), and Java for the modern JVM ecosystem.
- **WebAssembly.** The most requested modern target, and one the canonical compiler never had. WasmGC makes it practical for a garbage-collected language; Kotlin, Dart and OCaml already compile to it, with small binaries, host GC integration and direct JS interop. A proper wasm target covers browsers and server and edge runtimes through WASI. Until it lands, the Rust backend gives an interim wasm path.

PHP, Python and Lua also come forward as first-class targets, each one landing when its conformance suite passes rather than on a set date.

We're also looking at a few more, all of them normal source-output backends of the kind the Target SDK is meant to let the community own: Kotlin, building on the JVM work so Haxe fits into Android projects instead of just running on Android; TypeScript output separate from the JavaScript backend, so Haxe libraries can ship as typed npm packages; Go, for single-binary servers and edge deployment; and Swift, for native Apple interop. Each has real costs: Kotlin's null safety, TypeScript's structural types, Go's lack of inheritance, and Swift's reference counting, which doesn't match garbage collection. None of these are promised.

### Shaders

One thing in design isn't a normal target. A lot of people in this ecosystem write graphics code every day, in a separate shader language with separate types, and nothing checks it until it fails at runtime.

A shader target compiles a restricted subset of hx+ (no heap, no recursion, no dynamic dispatch) to SPIR-V, with WGSL, GLSL and HLSL alongside. What makes it useful is that the types on both sides become the same types, so uniforms, vertex attributes and buffer layouts are checked by the compiler instead of turning up as a black screen. Haxe's own history shows people want this, and other typed languages have shown it can be done. It has its own semantics and its own conformance tests, and it's only practical in a compiler people can extend.

### Tiers

Targets are grouped into tiers, the way Rust does for platforms. Tier 1 targets are maintained by the core team, and a release doesn't ship unless they pass full conformance: today that's eval, JavaScript, C++, cppia and JVM bytecode, plus the backends above as they mature. Tier 2 targets are maintained by their communities through the Target SDK. The compiler accepts their generators, the conformance suite measures them in public, and their release schedule is up to their maintainers. HashLink bytecode and Flash are here: welcome, but not promised. A Tier 2 target whose community keeps it conformant can move up.

There's one exception to keeping targets: hx+ retires the Neko VM. Neko is a custom runtime the ecosystem has to maintain by hand, and unlike the other targets it doesn't run on any widely used host. eval, cppia and HashLink cover everything it does, no products ship on it, and it mostly survives because haxelib runs on it, which the new tooling doesn't need. We'll retire a target nobody depends on, and we won't retire one people rely on.

### Phase 6: Engines

Most Haxe code that reaches players ships inside a game engine. Today using Haxe with the big engines means community bindings that work against the toolchain instead of with it. The community has already shown it can be done: [unreal.hx](https://github.com/proletariatgames/unreal.hx) put Haxe into Unreal Engine deeply enough for commercial games, and [HxGodot](https://github.com/HxGodot/hxgodot) brings Haxe to Godot 4 through GDExtension. Those projects deserve first-class support.

- **Unreal Engine:** building on the hxcpp approach unreal.hx proved, with Haxe classes as UCLASS types, Blueprint interop and full engine API access.
- **Godot:** the GDExtension route through hxcpp, as HxGodot does, with the Rust target as a second option as it matures.
- **Unity:** through the new C# target, with Haxe producing modern, idiomatic C# that Unity uses directly.

The goal is gameplay code written once in Haxe that moves between engines the same way Haxe code moves between platforms, with the integrations maintained in Haxe by the game developers who use them and tested the same way as every other target.

### Ongoing

Coroutines and structured async on the 4.3 base, more compile-time programming, more features through the RFC process, editions for long-term changes, and regular releases so progress shows up in the changelog.

## 10. Get involved

The compiler is out now, and the rest of this document will follow as working software, which is what matters. We're asking for three things:

- **Try it.** Install hxc with `haxelib install hxc` and point it at your existing build. Or open [haxe.run](https://haxe.run) and try it in the browser. It should just compile, and if it doesn't, that's a bug and we want to hear about it.
- **Argue with it.** The first RFCs open with the first release. If a feature is wrong, say so with a playground link that shows why. That's how the language will be run.
- **Build a target.** If there's a platform you need that the ecosystem doesn't have, the Target SDK and its conformance suite are there for that. You don't need anyone's permission.

Haxe's original idea, one language for every platform, is worth keeping, and we built the tools to keep it.

---

## FAQ

**Is this a fork of Haxe?**
No. hx+ contains Haxe 4.3. Your code compiles unchanged, and keeping it that way is the project's first commitment. hxc is a faithful Haxe 4.3 compiler, and hx+ is a strict superset on top of it.

**Where do I get hxc?**
From haxelib: `haxelib install hxc`, then `haxelib run hxc build.hxml`. The source is on [GitHub](https://github.com/dimensionscape/hxc). To try it without installing anything, open [haxe.run](https://haxe.run).

**Why not just contribute to the official compiler?**
The problem isn't a shortage of hands; it's structural. An OCaml codebase limits contributors to people who know both worlds well, and the project's direction is set under constraints we don't share. hxc changes the structure instead. Nothing is held back: everything we build is open, and MPL code can go into GPL projects, so upstream can take any of it.

**Will my existing code or libraries break?**
No. That's the promise the whole project is built around. Existing std APIs stay as they are for code on the 4.3 edition, new syntax uses contextual keywords only, changes are opt-in, and the few exceptions (security fixes, platforms dropping features) are published ahead of time.

**Will my editor and build setup keep working?**
Yes. hxc has the same command line and hxml support, works with existing haxelib setups, and speaks the same display and diagnostics protocol today's IDE plugins use.

**Why base it on 4.3 and not Haxe 5?**
Haxe 4.3 is the last release with the full set of targets, and the targets are the point. hx+ evolves on that base on its own schedule, and takes improvements from anywhere, Haxe 5 included, when they help.

**What about libraries that need Haxe 5?**
The biggest consumer frameworks still work on 4.x, and hx+ will add the 5.x features libraries actually depend on. Where upstream's new std APIs are well designed, hx+ matches them for source compatibility.

**Who controls hx+?**
An open RFC process, in public, with a working playground demo attached to every proposal. The compatibility rules above are commitments.

**What keeps hx+ from ending up in the same situation?**
Incentives and design. The people maintaining this toolchain ship the ecosystem's most used frameworks on it, so keeping it healthy isn't optional for us. It's also set up so it doesn't depend on a small group's attention: the compiler is written in the language its users already know, correctness is checked by test suites instead of living in a few people's heads, and targets are owned by the communities that need them.

---

*Author: Christopher Speciale, Dimensionscape LLC, maintainer of Lime and OpenFL.*
*Site: [hxplus.org](https://hxplus.org). Compiler: [github.com/dimensionscape/hxc](https://github.com/dimensionscape/hxc) and [haxelib](https://lib.haxe.org/p/hxc/). Playground: [haxe.run](https://haxe.run).*

### References

- Haxe 5.0.0-preview.1 release notes (target removals): https://github.com/HaxeFoundation/haxe/releases/tag/5.0.0-preview.1
- Haxe 4.3 release (last release with C#/Java targets): https://community.haxe.org/t/haxe-4-3-7-released/4611
- haxelib library index (lime/openfl download counts): https://lib.haxe.org/
- asys evolution proposal: https://github.com/HaxeFoundation/haxe-evolution/blob/master/proposals/0010-asys.md
- Haxe-in-Haxe notes, HaxeFoundation/haxe#6843 (2018): https://github.com/HaxeFoundation/haxe/issues/6843
- Rust bootstrap history (OCaml to self-hosted rustc): https://www.languagelineage.org/languages/rust
- Go 1.5 self-hosting toolchain: https://www.infoq.com/news/2015/08/go-1-5
- TypeScript native (Go) port announcement: https://devblogs.microsoft.com/typescript/typescript-native-port/
- Rust editions guide: https://doc.rust-lang.org/edition-guide/
- Go 1 compatibility promise: https://go.dev/doc/go1compat
- Community demand for a new C# target: https://community.haxe.org/t/a-new-c-target-for-haxe-5/4764
- unreal.hx, Haxe integration for Unreal Engine: https://github.com/proletariatgames/unreal.hx
- HxGodot, Haxe GDExtension for Godot 4: https://github.com/HxGodot/hxgodot
