@extends('layouts.app')

@section('content')
<div class="container">
    {!! Form::open(['route' => ['posts.update', $post->id], 'method' => 'PUT', 'class' => 'form-horizontal', 'files' => true]) !!}

        <div class="form-group">
            {!! Form::label('title', 'Post Title') !!}
            {!! Form::text('title', $post->title, ['class' => 'form-control', 'placeholder' => 'Enter title']) !!}
        </div>

        <div class="form-group">
            {!! Form::label('body', 'Body') !!}
            {!! Form::textarea('body', $post->body, ['class' => 'form-control', 'rows' => 5]) !!}
        </div>

        <div class="form-group">
            {!! Form::select('category_id', $categories, $post->category_id, ['class' => 'form-control']) !!}
        </div>

        <div class="form-group">
            {!! Form::checkbox('published', 1, $post->published) !!}
            {!! Form::label('published', 'Published') !!}
        </div>

        {!! Form::submit('Update Post', ['class' => 'btn btn-primary']) !!}
    {!! Form::close() !!}

    {!! link_to_route('posts.index', 'Back to list', [], ['class' => 'btn btn-link']) !!}
</div>
@endsection
