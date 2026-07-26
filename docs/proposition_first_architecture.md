# Proposition-First Architecture (Materialized View)

> **⚠️ AVISO DE ARQUITECTURA:** Este documento ha sido atomizado. 
> La arquitectura central está formalizada en el SSOT de átomos en `TractatusKnowledgeMachine/atoms/`.

## Core stance (Proposición Primero)
Matrix es `proposition-first`, no `object-property-first`. La unidad lógica primitiva es la `Proposition` canónica `(R a b)`.

## El Cambio de Paradigma Tensorial
El diseño operacional ya no permite que el estado (los hechos) viva encapsulado dentro de particiones locales (`WiGame`). 
La arquitectura actual se basa en un **[[Hipertensor_Canonico]]** global desde el cual se extraen **Proyecciones Matriciales** locales.

## Piezas Operacionales Canónicas
* [[Hipertensor_Canonico]]: Central SSOT of Facts.
* [[WiGame]]: Local View / Projection.
* [[Proposition]] / [[Fact]]: The logical data units.
* [[Thing]] / [[Relation]] / [[Symbol]]: The dimensions of the space.

*(Dirígete al grafo de átomos en `sldb` para explorar las relaciones estructurales de estas piezas).*
